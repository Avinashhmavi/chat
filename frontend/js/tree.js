// tree.js
// Modular Conversation Tree Visualization for T.I.M.E. Chatbot
// Requirements: D3.js (v7+), see tree.css for styles
// To enable: include <script src="tree.js"></script> and <link rel="stylesheet" href="tree.css"> in your HTML
// To remove: delete/comment out the above tags and the #tree-container div
// Author: AiGENThix

(function(window, document, d3) {
    'use strict';
    // TreeModule namespace
    const TreeModule = {};
    let treeData = null;
    let treeRoot = null;
    let svg = null;
    let g = null;
    let width = 400;
    let height = 400;
    let nodeId = 0;
    let container = null;
    let qaCache = {};
    let lastState = null;
    let isInitialized = false;
    let debug = true;
    let config = {
        containerId: 'tree-container',
        qaEndpoint: '/api/category_qa',
        transitionDuration: 400,
        nodeRadius: 12,
        siblingSeparation: 1.2,
        levelSeparation: 50
    };
    let zoom = null;
    let zoomGroup = null;
    let boxPadding = { x: 12, y: 8 };
    let boxMinWidth = 60;
    let boxHeight = 32;
    let horizontalSpacing = 120;
    let verticalSpacing = 70;

    // Utility: Debug log
    function log(...args) {
        if (debug) console.log('[TreeModule]', ...args);
    }

    // Utility: Deep clone
    function deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    // Utility: Find node by id
    function findNodeById(node, id) {
        if (node.id === id) return node;
        if (!node.children) return null;
        for (let child of node.children) {
            let found = findNodeById(child, id);
            if (found) return found;
        }
        return null;
    }

    // Utility: Find path to node
    function findPathToNode(node, id, path=[]) {
        if (node.id === id) return [...path, node];
        if (!node.children) return null;
        for (let child of node.children) {
            let res = findPathToNode(child, id, [...path, node]);
            if (res) return res;
        }
        return null;
    }

    // Utility: Remove all children after a node (rewind)
    function pruneAfterNode(node) {
        node.children = [];
    }

    // Utility: Remove duplicate nodes in a path
    function hasDuplicateInPath(path, label) {
        return path.some(n => n.label === label);
    }

    // Initialize the tree
    TreeModule.init = function(options = {}) {
        if (isInitialized) return;
        config = {...config, ...options};
        container = document.getElementById(config.containerId);
        if (!container) {
            log('No tree container found, aborting init.');
            return;
        }
        // Clear container
        container.innerHTML = '';
        // Set up SVG
        width = container.offsetWidth || 900;
        height = container.offsetHeight || 600;
        svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'tree-svg');
        // Add zoomable group
        zoomGroup = svg.append('g').attr('class', 'zoom-group');
        g = zoomGroup.append('g').attr('class', 'tree-main-group');
        // D3 zoom behavior
        zoom = d3.zoom()
            .scaleExtent([0.3, 2.5])
            .on('zoom', (event) => {
                zoomGroup.attr('transform', event.transform);
            });
        svg.call(zoom);
        // Center the tree initially
        svg.call(zoom.transform, d3.zoomIdentity.translate(width/2, 40));
        treeData = null;
        treeRoot = null;
        nodeId = 0;
        qaCache = {};
        lastState = null;
        isInitialized = true;
        log('Tree initialized.');
    };

    // Destroy the tree and clean up
    TreeModule.destroy = function() {
        if (!isInitialized) return;
        if (container) container.innerHTML = '';
        svg = null;
        g = null;
        treeData = null;
        treeRoot = null;
        nodeId = 0;
        qaCache = {};
        lastState = null;
        isInitialized = false;
        log('Tree destroyed.');
    };

    // Utility: Find or create a child node by label
    function findOrCreateChild(parent, label, state, options) {
        if (!parent.children) parent.children = [];
        let existing = parent.children.find(child => child.label === label);
        if (existing) return existing;
        let newNode = {
            id: ++nodeId,
            label: label,
            state: state,
            options: options || [],
            isChosen: false,
            children: []
        };
        parent.children.push(newNode);
        return newNode;
    }

    // Add a node to the tree (called after each user selection)
    // context: object { label, previousState, nextState, options }
    TreeModule.addNode = function(context) {
        log('addNode called with context:', context);
        const { label, previousState, nextState, options } = context;

        if (!isInitialized) return;
        if (!label) return;

        if (!treeData) {
            // Tree has not started yet. Check if this is the moment.
            if (previousState === 'course_selected') {
                log('Tree starting with root node:', label);
                treeData = {
                    id: ++nodeId,
                    label: label,
                    state: nextState,
                    options: options,
                    isChosen: true,
                    children: []
                };
            } else {
                log('Tree start deferred. Previous state was not "course_selected".');
                return; // Exit, not time to start yet.
            }
        } else {
            // Tree exists, find the parent node to add children to.
            let parentNode = findNodeById(treeData, nodeId);
            if (!parentNode) {
                log('Error: Could not find the current node in the tree. Resetting.', 'Current Node ID:', nodeId);
                treeData = null; // Reset the tree to be safe
                return;
            }

            // Mark all existing children of the parent as not chosen
            if (parentNode.children) {
                parentNode.children.forEach(child => child.isChosen = false);
            }

            // Find or create the newly selected child
            let selectedChild = findOrCreateChild(parentNode, label, nextState, options);
            selectedChild.isChosen = true;
            nodeId = selectedChild.id; // Update current node ID

            // Add all other options as unchosen children to the parent
            if (parentNode.options) {
                parentNode.options.forEach(opt => {
                    if (opt !== label) {
                        findOrCreateChild(parentNode, opt, parentNode.state, []);
                    }
                });
            }

            // And now, pre-populate the *next* layer of branches from the newly selected node
            if (selectedChild.options) {
                selectedChild.options.forEach(opt => {
                    findOrCreateChild(selectedChild, opt, nextState, []);
                });
            }
        }

        lastState = nextState;
        updateTree();
    };

    // Rewind to a previous node (by id)
    function rewindToNode(id) {
        let path = findPathToNode(treeData, id, []);
        if (!path) return;
        let nodeData = path[path.length - 1];

        // Prune the tree
        pruneAfterNode(nodeData);
        nodeId = nodeData.id;
        lastState = nodeData.state;
        log('Rewound to node:', nodeData.label);

        // Re-render the tree visually
        updateTree();

        // Fire a custom event to notify the chatbot to rewind its state
        let evt = new CustomEvent('tree:rewind', {
            detail: {
                label: nodeData.label,
                state: nodeData.state,
                context: nodeData.context
            }
        });
        window.dispatchEvent(evt);
        log('Dispatched tree:rewind event for state:', nodeData.state);
    }

    // Jump to a sibling/alternative branch
    function jumpToSibling(id, siblingLabel) {
        let path = findPathToNode(treeData, id, []);
        if (!path) return;
        let parent = path[path.length - 2];
        if (!parent) return;
        // Remove all children after parent
        pruneAfterNode(parent);
        nodeId = parent.id;
        lastState = parent.state;
        // Add new branch
        TreeModule.addNode({ label: siblingLabel, previousState: parent.state, nextState: parent.state, options: [] });
        log('Jumped to sibling branch:', siblingLabel);
    }

    // Fetch Q&A for a category node
    function fetchQA(label, cb) {
        if (qaCache[label]) {
            cb(qaCache[label]);
            return;
        }
        fetch(config.qaEndpoint + '?category=' + encodeURIComponent(label))
            .then(r => r.json())
            .then(data => {
                qaCache[label] = data;
                cb(data);
            })
            .catch(() => {
                cb([]);
            });
    }

    // Render Q&A boxes below a category node
    function renderQA(node, x, y) {
        // Remove old Q&A
        d3.select(container).selectAll('.qa-box').remove();
        fetchQA(node.label, function(qaList) {
            if (!qaList || !qaList.length) return;
            let qaG = d3.select(container)
                .append('div')
                .attr('class', 'qa-box')
                .style('position', 'absolute')
                .style('left', (x + 60) + 'px')
                .style('top', (y + 40) + 'px');
            qaList.forEach(qa => {
                let box = document.createElement('div');
                box.className = 'qa-item';
                box.innerHTML = `<div class='qa-q'>Q: ${qa.question}</div><div class='qa-a'>A: ${qa.answer}</div>`;
                qaG.node().appendChild(box);
            });
            log('Q&A rendered for:', node.label);
        });
    }

    // Main tree update/render function
    function updateTree() {
        log('updateTree called. Current treeData:', deepClone(treeData));
        if (!treeData) return;
        g.selectAll('*').remove(); // Clear previous render
        // D3 tree layout
        let root = d3.hierarchy(treeData);

        // Assign initial positions to every node
        let treeLayout = d3.tree().nodeSize([horizontalSpacing, verticalSpacing]);
        treeLayout(root);

        // --- Overlap Prevention ---
        // Second pass to adjust x-positions based on actual node widths
        root.eachAfter(node => {
            if (node.children) {
                let totalChildWidth = 0;
                node.children.forEach(child => {
                    const textWidth = child.data.label.length * 8; // Estimate text width
                    child.data._boxWidth = Math.max(textWidth + boxPadding.x * 2, boxMinWidth);
                    totalChildWidth += child.data._boxWidth;
                });

                let startX = node.x - (totalChildWidth + (node.children.length - 1) * 20) / 2; // 20 is padding

                node.children.forEach(child => {
                    child.x = startX + child.data._boxWidth / 2;
                    startX += child.data._boxWidth + 20; // Move to next position
                });
            }
        });
        // --- End Overlap Prevention ---

        // Center the tree view on the current node
        let currentD3Node = root.descendants().find(d => d.data.id === nodeId);
        if (currentD3Node && zoom) {
            const transform = d3.zoomIdentity
                .translate(width / 2 - currentD3Node.x, height / 2 - currentD3Node.y)
                .scale(1); // You can adjust the scale here if you want
            svg.transition().duration(config.transitionDuration).call(zoom.transform, transform);
        }

        // Draw links
        g.selectAll('.link')
            .data(root.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y + boxHeight / 2)
            );
        // Draw nodes as rectangles
        let node = g.selectAll('.node')
            .data(root.descendants())
            .enter()
            .append('g')
            .attr('class', d => `node ${d.data.isChosen ? 'node-chosen' : 'node-option'} ${d.data.id === nodeId ? 'node-current' : ''}`)
            .attr('transform', d => `translate(${d.x},${d.y})`)
            .on('click', function(event, d) {
                event.stopPropagation();
                if (d.data.id === nodeId) return;
                if (d.data.isChosen) {
                    rewindToNode(d.data.id);
                } else {
                    let jumpEvt = new CustomEvent('tree:branch-jump', {
                        detail: {
                            label: d.data.label,
                            state: d.parent.data.state,
                        }
                    });
                    window.dispatchEvent(jumpEvt);
                }
            });
        // Draw rectangles sized to fit text
        node.append('rect')
            .attr('transform', function(d) {
                // Use pre-calculated width, or calculate if not present
                let boxWidth = d.data._boxWidth || Math.max((d.data.label || '').length * 8 + boxPadding.x * 2, boxMinWidth);
                d.data._boxWidth = boxWidth;
                return `translate(${-boxWidth / 2}, 0)`;
            })
            .attr('width', d => d.data._boxWidth)
            .attr('height', boxHeight)
            .attr('rx', 8)
            .attr('ry', 8);
        // Draw text inside rectangles
        node.append('text')
            .attr('y', boxHeight / 2)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .text(d => d.data.label);
        // Q&A double-click
        node.filter(d => d.data.options && d.data.options.length > 0 && (!d.children || d.children.length === 0))
            .on('dblclick', function(event, d) {
                event.stopPropagation();
                log(`Fetching Q&A for category: ${d.data.label}`);
                renderQA(d.data, d.x, d.y);
            });
        log('Tree rendered.');
    }

    // Expose public API
    window.TreeModule = {
        init: TreeModule.init,
        destroy: TreeModule.destroy,
        addNode: TreeModule.addNode
    };

    // Defer initialization until the DOM is fully loaded to prevent race conditions.
    document.addEventListener('DOMContentLoaded', () => {
        // Auto-init if container exists
        if (document.getElementById(config.containerId)) {
            TreeModule.init();
        }
    });

})(window, document, window.d3); 