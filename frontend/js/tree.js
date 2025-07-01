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
    let horizontalSpacing = 220;
    let verticalSpacing = 120;
    let categoryMap = {};
    let hiddenDiv = null; // For measuring HTML content

    // Utility: Debug log
    function log(...args) {
        if (debug) console.log('[TreeModule]', ...args);
    }

    // Utility: Deep clone
    function deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    // Utility: Create hidden div for measuring HTML content
    function createHiddenDiv() {
        if (!hiddenDiv) {
            hiddenDiv = document.createElement('div');
            hiddenDiv.style.position = 'absolute';
            hiddenDiv.style.visibility = 'hidden';
            hiddenDiv.style.whiteSpace = 'nowrap';
            hiddenDiv.style.fontFamily = 'Arial, sans-serif';
            hiddenDiv.style.fontSize = '14px';
            hiddenDiv.style.lineHeight = '1.4';
            hiddenDiv.style.maxWidth = '300px';
            hiddenDiv.style.wordWrap = 'break-word';
            hiddenDiv.style.overflowWrap = 'break-word';
            document.body.appendChild(hiddenDiv);
        }
        return hiddenDiv;
    }

    // Utility: Measure HTML content dimensions
    function measureHtmlContent(htmlContent, maxWidth = 300) {
        const div = createHiddenDiv();
        div.innerHTML = htmlContent;
        div.style.maxWidth = maxWidth + 'px';
        
        // Force layout calculation
        div.style.display = 'block';
        const rect = div.getBoundingClientRect();
        div.style.display = 'none';
        
        return {
            width: Math.max(rect.width + boxPadding.x * 2, boxMinWidth),
            height: Math.max(rect.height + boxPadding.y * 2, boxHeight)
        };
    }

    // Utility: Check if content contains HTML
    function containsHtml(text) {
        return /<[^>]+>/.test(text);
    }

    // Utility: Check if browser supports foreignObject
    function supportsForeignObject() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
        return !!foreignObject;
    }

    // Utility: Strip HTML tags for fallback rendering
    function stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
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

    // Utility: Find node by label (first match, depth-first)
    function findNodeByLabel(node, label) {
        if (node.label === label) return node;
        if (!node.children) return null;
        for (let child of node.children) {
            let found = findNodeByLabel(child, label);
            if (found) return found;
        }
        return null;
    }

    // Utility: Prune all children and siblings after a node
    function pruneSiblingsAndChildren(node, parent) {
        if (!parent || !parent.children) return;
        parent.children = parent.children.filter(child => child === node);
        node.children = [];
    }

    // Extract context from the tree path
    function getContextFromNode(node) {
        let context = {};
        let current = node;
        while (current) {
            if (current.state === "city_selected") context.city = current.label;
            else if (current.state === "course_selected") context.course = current.label;
            else if (current.state === "subcourse_selected") context.subcourse = current.label;
            else if (current.state === "training_type_selected") context.training_type = current.label;
            current = findNodeById(treeData, current.id)?.parent;
        }
        return context;
    }

    // Fetch questions and answers for a category and add them as nodes
    async function fetchAndAddQA(categoryNode) {
        const categoryId = categoryMap[categoryNode.label];
        if (!categoryId) {
            log('No category ID found for:', categoryNode.label);
            return;
        }
        if (!window.userId) {
            log('No userId available for category:', categoryNode.label);
            alert('Please complete registration to view category answers.');
            return;
        }
        try {
            log('Fetching questions for category:', categoryNode.label, 'categoryId:', categoryId);
            // Fetch all questions for the category
            const response = await fetch(`/api/questions_dict?category_id=${categoryId}`);
            const data = await response.json();
            log('[TreeModule] /api/questions_dict response:', data);
            if (!data.success || !data.data) {
                log('Failed to fetch questions for category:', categoryNode.label, data);
                return;
            }
            // Set category context via /chat
            const contextPayload = {
                state: 'category_selected',
                input: categoryNode.label,
                user_id: window.userId
            };
            const contextResponse = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(contextPayload)
            });
            const contextData = await contextResponse.json();
            log('[TreeModule] Category context response:', contextData);
            if (!contextData.options || !contextData.options.length) {
                log('Failed to set category context - no options returned:', contextData);
                return;
            }
            log('[TreeModule] Category context set successfully, proceeding with Q&A fetch');
            // Batch fetch answers for all questions
            for (const [question, questionId] of Object.entries(data.data)) {
                const questionNode = findOrCreateChild(categoryNode, question, 'question_selected', []);
                questionNode.data = { question_id: questionId };
                log('[TreeModule] Created question node:', question);
                // Fetch answer via /chat
                const answerPayload = {
                    state: 'question_selected',
                    input: question,
                    user_id: window.userId
                };
                const answerResponse = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(answerPayload)
                });
                const answerData = await answerResponse.json();
                log('[TreeModule] /chat answer response for question:', question, answerData);
                if (answerData.response) {
                    // Store the raw HTML response instead of stripping it
                    const answerNode = findOrCreateChild(questionNode, answerData.response, answerData.next_state || 'answer', answerData.options || []);
                    answerNode.data = { raw_response: answerData.response };
                    log('[TreeModule] Added answer node for question:', question, 'answer:', answerData.response);
                    // Handle subquestions recursively
                    if (answerData.options && answerData.options.length > 0 && answerData.next_state !== 'question_selected') {
                        for (const subOption of answerData.options) {
                            const subQuestionNode = findOrCreateChild(answerNode, subOption, answerData.next_state, []);
                            await fetchSubAnswer(subQuestionNode, answerNode, { ...contextPayload });
                        }
                    }
                } else {
                    log('[TreeModule] Failed to fetch answer for question:', question, answerData);
                }
            }
            updateTree(); // Update tree after all questions and answers are added
        } catch (error) {
            console.error('[TreeModule] Error fetching Q&A:', error);
        }
    }

    // Fetch subquestion answers recursively
    async function fetchSubAnswer(subQuestionNode, parentNode, context) {
        if (!window.userId) {
            log('No userId available for subquestion:', subQuestionNode.label);
            alert('Please complete registration to view subquestion answers.');
            return;
        }
        try {
            const payload = {
                state: subQuestionNode.state,
                input: subQuestionNode.label,
                user_id: window.userId
            };
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            log('[TreeModule] /chat subanswer response for:', subQuestionNode.label, data);
            if (data.response) {
                // Store the raw HTML response instead of stripping it
                const answerNode = findOrCreateChild(subQuestionNode, data.response, data.next_state || 'answer', data.options || []);
                answerNode.data = { raw_response: data.response };
                log('[TreeModule] Added subanswer node:', data.response);
                updateTree();
                // Continue recursion if more options exist
                if (data.options && data.options.length > 0 && data.next_state !== 'question_selected') {
                    for (const subSubOption of data.options) {
                        const subSubQuestionNode = findOrCreateChild(answerNode, subSubOption, data.next_state, []);
                        await fetchSubAnswer(subSubQuestionNode, subQuestionNode, context);
                    }
                }
            } else {
                log('[TreeModule] Failed to fetch subanswer for:', subQuestionNode.label, data);
            }
        } catch (error) {
            console.error('[TreeModule] Error fetching subanswer:', error);
        }
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
        container.innerHTML = '';
        width = container.offsetWidth || 900;
        height = container.offsetHeight || 600;
        svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('class', 'tree-svg');
        zoomGroup = svg.append('g').attr('class', 'zoom-group');
        g = zoomGroup.append('g').attr('class', 'tree-main-group');
        zoom = d3.zoom()
            .scaleExtent([0.3, 2.5])
            .on('zoom', (event) => {
                zoomGroup.attr('transform', event.transform);
            });
        svg.call(zoom);
        svg.call(zoom.transform, d3.zoomIdentity.translate(width/2, 40));
        treeData = null;
        treeRoot = null;
        nodeId = 0;
        qaCache = {};
        lastState = null;
        isInitialized = true;
        log('Tree initialized.');

        fetch('/api/categories_dict')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    categoryMap = data.data;
                    log('Categories fetched:', categoryMap);
                }
            })
            .catch(error => console.log('Error fetching categories:', error));
    };

    // Destroy the tree and clean up
    TreeModule.destroy = function() {
        if (!isInitialized) return;
        if (container) container.innerHTML = '';
        if (hiddenDiv && hiddenDiv.parentNode) {
            hiddenDiv.parentNode.removeChild(hiddenDiv);
            hiddenDiv = null;
        }
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
    function findOrCreateChild(parent, label, state, options, id = null) {
        if (!parent.children) parent.children = [];
        let existing = null;
        if (id !== null) {
            existing = parent.children.find(child => child.id === id);
        }
        if (!existing) {
            existing = parent.children.find(child => child.label === label);
        }
        if (existing) {
            // Always update state if provided
            if (state && existing.state !== state) existing.state = state;
            return existing;
        }
        let newNode = {
            id: id !== null ? id : ++nodeId,
            label: label,
            state: state || '',
            options: options || [],
            isChosen: false,
            children: []
        };
        parent.children.push(newNode);
        return newNode;
    }

    // Utility: Find node by a path of IDs
    function findNodeByPath(root, path) {
        let node = root;
        for (let i = 1; i < path.length; i++) { // skip root
            if (!node.children) return null;
            node = node.children.find(child => child.id === path[i]);
            if (!node) return null;
        }
        return node;
    }

    // Helper to recursively clear all descendants of a node
    function clearAllDescendants(node) {
        if (node.children && node.children.length > 0) {
            node.children.forEach(child => clearAllDescendants(child));
            node.children = [];
        }
    }

    // Utility: Ensure the full path exists in the tree, creating missing nodes as needed
    function ensurePathExists(root, path, labels, states, optionsArr, context) {
        let node = root;
        for (let i = 1; i < path.length; i++) {
            if (!node.children) node.children = [];
            // --- Robust label resolution ---
            let label = labels[i];
            // Try to get label from parent's options if available
            if ((!label || label.startsWith('Node ')) && node.options && Array.isArray(node.options)) {
                if (typeof node.options[0] === 'string') {
                    label = node.options.find(opt => makeNodeId(opt) === path[i]) || label;
                }
                if (typeof node.options[0] === 'object') {
                    let found = node.options.find(opt => makeNodeId(opt.label) === path[i] || opt.id === path[i]);
                    if (found) label = found.label;
                }
            }
            // If still not found, check all children of all siblings for a matching id/label
            if ((!label || label.startsWith('Node ')) && node.children && node.children.length > 0) {
                for (let sib of node.children) {
                    if (sib.id === path[i]) {
                        label = sib.label;
                        break;
                    }
                    if (sib.children && sib.children.length > 0) {
                        let found = sib.children.find(child => child.id === path[i]);
                        if (found) {
                            label = found.label;
                            break;
                        }
                    }
                }
            }
            // Always use the label from context for the last node
            if (i === path.length - 1 && context && context.label) {
                label = context.label;
            }
            // If still not found, try to get label from parent's options (object type)
            if ((!label || label.startsWith('Node ')) && node.options && Array.isArray(node.options)) {
                if (typeof node.options[0] === 'object') {
                    let found = node.options.find(opt => opt.id === path[i]);
                    if (found) label = found.label;
                }
            }
            let state = states[i] || (context && context.nextState) || '';
            let child = node.children.find(child => child.id === path[i]);
            if (!child) {
                child = {
                    id: path[i],
                    label: label || `Node ${path[i]}`,
                    state: state,
                    options: optionsArr[i] || [],
                    isChosen: false,
                    children: []
                };
                node.children.push(child);
            } else {
                // Always update state if provided
                if (state && child.state !== state) child.state = state;
                if (label && child.label !== label) child.label = label;
            }
            // --- Prune siblings at this level ---
            // Special handling for category level: do not remove category siblings, only collapse their descendants
            if (state === 'category_selected' && node.children.length > 1) {
                node.children.forEach(sib => {
                    if (sib.id !== path[i]) {
                        sib.isChosen = false;
                        clearAllDescendants(sib);
                    } else {
                        sib.isChosen = true;
                    }
                });
            } else {
                node.children.forEach(sib => {
                    if (sib.id !== path[i]) {
                        sib.isChosen = false;
                        clearAllDescendants(sib);
                    } else {
                        sib.isChosen = true;
                    }
                });
            }
            node = child;
        }
        return node;
    }

    // Helper to match backend's make_node_id logic for string labels
    function makeNodeId(label) {
        // Use a simple hash for demo; backend uses sha256 and mod 10^8
        let hash = 0;
        for (let i = 0; i < label.length; i++) {
            hash = ((hash << 5) - hash) + label.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash) % 100000000;
    }

    // Add a node to the tree
    TreeModule.addNode = function(context) {
        log('addNode called with context:', context);
        const { label, previousState, nextState, options, path } = context;

        if (!isInitialized) return;
        if (!label) return;

        // Only start tree at course_selected
        if (!treeData) {
            if (previousState === 'course_selected') {
                log('Tree starting with root node:', label);
                treeData = {
                    id: path && path.length > 0 ? path[0] : ++nodeId,
                    label: label,
                    state: nextState,
                    options: options,
                    isChosen: true,
                    children: []
                };
                nodeId = treeData.id;
                // Immediately add subcourse options as children
                if (options && Array.isArray(options)) {
                    options.forEach(opt => {
                        findOrCreateChild(treeData, opt, nextState, [], null);
                    });
                }
            } else {
                log('Tree start deferred. Previous state was not "course_selected".');
                return;
            }
        } else {
            if (!path || path.length < 1) {
                log('Error: No path provided in context.');
                return;
            }
            // Remove all deeper branches if the new path is shorter than the previous one
            if (window._lastTreePath && window._lastTreePath.length > path.length) {
                let node = treeData;
                for (let i = 1; i < path.length; i++) {
                    node = node.children && node.children.find(child => child.id === path[i]);
                    if (!node) break;
                }
                if (node && node.children) node.children = [];
            }
            window._lastTreePath = path.slice();
            // Build up the path of labels, states, and options for each node in the path
            let labels = [];
            let states = [];
            let optionsArr = [];
            let current = treeData;
            labels.push(current.label);
            states.push(current.state);
            optionsArr.push(current.options);
            for (let i = 1; i < path.length; i++) {
                let found = current.children && current.children.find(child => child.id === path[i]);
                if (found) {
                    labels.push(found.label);
                    states.push(found.state);
                    optionsArr.push(found.options);
                    current = found;
                } else {
                    labels.push('');
                    states.push('');
                    optionsArr.push([]);
                }
            }
            // Ensure the full path exists and prune siblings at every level
            let selectedNode = ensurePathExists(treeData, path, labels, states, optionsArr, context);
            // At the selected node, clear its children and add new children for options
            if (selectedNode) {
                selectedNode.children = [];
                if (options && Array.isArray(options)) {
                    options.forEach(opt => {
                        findOrCreateChild(selectedNode, opt, nextState, [], null);
                    });
                }
                selectedNode.isChosen = true;
                nodeId = selectedNode.id;
                if (categoryMap[selectedNode.label]) {
                    fetchAndAddQA(selectedNode);
                }
            }
        }
        lastState = nextState;
        updateTree();
    };

    // Rewind to a previous node
    function rewindToNode(id) {
        let path = findPathToNode(treeData, id, []);
        if (!path) return;
        let nodeData = path[path.length - 1];
        let parent = path.length > 1 ? path[path.length - 2] : null;
        if (parent && parent.children) {
            parent.children = [nodeData];
        }
        nodeId = nodeData.id;
        lastState = nodeData.state;
        log('Rewound to node:', nodeData.label);
        updateTree();
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
    function jumpToSibling(id, siblingLabel, siblingPath) {
        // siblingPath: path of IDs to the parent, plus the sibling's ID as last element
        if (!siblingPath || siblingPath.length < 2) return;
        let parent = findNodeByPath(treeData, siblingPath.slice(0, -1));
        if (!parent) return;
        // Prune all children except the sibling
        let siblingNode = parent.children.find(child => child.label === siblingLabel);
        if (!siblingNode) {
            siblingNode = findOrCreateChild(parent, siblingLabel, parent.state, []);
        }
        parent.children = [siblingNode];
        nodeId = siblingNode.id;
        lastState = siblingNode.state;
        TreeModule.addNode({ label: siblingLabel, previousState: parent.state, nextState: parent.state, options: [], path: siblingPath });
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
        g.selectAll('*').remove();
        let root = d3.hierarchy(treeData);
        
        // Pre-calculate node dimensions for all nodes
        root.eachAfter(node => {
            const content = node.data.label;
            if (containsHtml(content) && supportsForeignObject()) {
                // For HTML content, measure the actual rendered size
                const dimensions = measureHtmlContent(content);
                node.data._boxWidth = dimensions.width;
                node.data._boxHeight = dimensions.height;
            } else {
                // For plain text or when foreignObject is not supported, use character-based calculation
                const textContent = containsHtml(content) ? stripHtml(content) : content;
                const textWidth = textContent.length * 8;
                node.data._boxWidth = Math.max(textWidth + boxPadding.x * 2, boxMinWidth);
                node.data._boxHeight = boxHeight;
            }
        });

        // Use ultra-tight D3 layout horizontally, but fixed vertical spacing for initial layout
        let treeLayout = d3.tree().nodeSize([horizontalSpacing, verticalSpacing]);
        treeLayout(root);

        // True overlap detection and minimal adjustment (horizontal only)
        const maxDepth = d3.max(root.descendants(), d => d.depth);
        const overlapPadding = 4;
        for (let pass = 0; pass < 4; pass++) {
            for (let level = 0; level <= maxDepth; level++) {
                const levelNodes = getNodesAtLevel(root, level);
                if (levelNodes.length <= 1) continue;
                // Sort by x
                levelNodes.sort((a, b) => a.x - b.x);
                for (let i = 0; i < levelNodes.length - 1; i++) {
                    const a = levelNodes[i];
                    const b = levelNodes[i + 1];
                    const aRight = a.x + (a.data._boxWidth || boxMinWidth) / 2;
                    const bLeft = b.x - (b.data._boxWidth || boxMinWidth) / 2;
                    if (aRight + overlapPadding > bLeft) {
                        // Nudge b and all nodes to its right
                        const nudge = aRight + overlapPadding - bLeft;
                        for (let j = i + 1; j < levelNodes.length; j++) {
                            levelNodes[j].x += nudge;
                        }
                    }
                }
            }
        }

        // --- Diagonal/parent-child vertical adjustment ---
        function adjustVerticalPositions(node) {
            if (!node.children || node.children.length === 0) return;
            // Sort children by y
            node.children.sort((a, b) => a.y - b.y);
            let currentY = node.y + (node.data._boxHeight || boxHeight) + 30; // 30px gap below parent
            for (let i = 0; i < node.children.length; i++) {
                const child = node.children[i];
                // If this child would overlap the previous, nudge it down
                if (i > 0) {
                    const prev = node.children[i - 1];
                    const prevBottom = prev.y + (prev.data._boxHeight || boxHeight) / 2;
                    const childTop = child.y - (child.data._boxHeight || boxHeight) / 2;
                    if (prevBottom + 10 > childTop) { // 10px vertical gap
                        const nudge = prevBottom + 10 - childTop;
                        child.y += nudge;
                    }
                }
                // Ensure child is at least below the parent
                if (child.y < currentY + (child.data._boxHeight || boxHeight) / 2) {
                    child.y = currentY + (child.data._boxHeight || boxHeight) / 2;
                }
                // Recursively adjust children
                adjustVerticalPositions(child);
                // Update currentY for next child
                currentY = child.y + (child.data._boxHeight || boxHeight) / 2;
            }
        }
        adjustVerticalPositions(root);

        // --- GLOBAL VERTICAL OVERLAP RESOLUTION ---
        function globalVerticalOverlapResolution() {
            const allNodes = root.descendants().sort((a, b) => a.y - b.y);
            const vertPad = 10;
            for (let pass = 0; pass < 4; pass++) {
                for (let i = 0; i < allNodes.length - 1; i++) {
                    const a = allNodes[i];
                    const aTop = a.y - (a.data._boxHeight || boxHeight) / 2;
                    const aBottom = a.y + (a.data._boxHeight || boxHeight) / 2;
                    for (let j = i + 1; j < allNodes.length; j++) {
                        const b = allNodes[j];
                        // Only check if horizontally close enough to possibly overlap
                        const aLeft = a.x - (a.data._boxWidth || boxMinWidth) / 2;
                        const aRight = a.x + (a.data._boxWidth || boxMinWidth) / 2;
                        const bLeft = b.x - (b.data._boxWidth || boxMinWidth) / 2;
                        const bRight = b.x + (b.data._boxWidth || boxMinWidth) / 2;
                        const horizontalOverlap = aRight > bLeft && bRight > aLeft;
                        if (!horizontalOverlap) continue;
                        const bTop = b.y - (b.data._boxHeight || boxHeight) / 2;
                        if (aBottom + vertPad > bTop) {
                            // Nudge b and all nodes below it
                            const nudge = aBottom + vertPad - bTop;
                            for (let k = j; k < allNodes.length; k++) {
                                allNodes[k].y += nudge;
                            }
                        }
                    }
                }
            }
        }
        globalVerticalOverlapResolution();
        // --- END GLOBAL VERTICAL OVERLAP RESOLUTION ---

        // Center parents over children (but don't over-adjust)
        adjustParentPositions(root);

        // Adjust SVG width if tree is very wide
        adjustSvgWidth(root);

        let currentD3Node = root.descendants().find(d => d.data.id === nodeId);
        if (currentD3Node && zoom) {
            const transform = d3.zoomIdentity
                .translate(width / 2 - currentD3Node.x, height / 2 - currentD3Node.y)
                .scale(1);
            svg.transition().duration(config.transitionDuration).call(zoom.transform, transform);
        }

        g.selectAll('.link')
            .data(root.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y + (d.data._boxHeight || boxHeight) / 2)
            );

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
                            state: d.data.state
                        }
                    });
                    window.dispatchEvent(jumpEvt);
                }
            });

        // Create background rectangle
        node.append('rect')
            .attr('transform', function(d) {
                const boxWidth = d.data._boxWidth || boxMinWidth;
                const nodeHeight = d.data._boxHeight || boxHeight;
                return `translate(${-boxWidth / 2}, 0)`;
            })
            .attr('width', d => d.data._boxWidth || boxMinWidth)
            .attr('height', d => d.data._boxHeight || boxHeight)
            .attr('rx', 8)
            .attr('ry', 8);

        // Render content - either as HTML or plain text
        node.each(function(d) {
            const nodeElement = d3.select(this);
            const content = d.data.label;
            const boxWidth = d.data._boxWidth || boxMinWidth;
            const nodeHeight = d.data._boxHeight || boxHeight;
            
            if (containsHtml(content) && supportsForeignObject()) {
                // Render HTML content using foreignObject
                const foreignObject = nodeElement.append('foreignObject')
                    .attr('x', -boxWidth / 2)
                    .attr('y', 0)
                    .attr('width', boxWidth)
                    .attr('height', nodeHeight);
                
                const htmlDiv = foreignObject.append('xhtml:div')
                    .style('width', '100%')
                    .style('height', '100%')
                    .style('display', 'flex')
                    .style('align-items', 'center')
                    .style('justify-content', 'center')
                    .style('padding', '8px')
                    .style('box-sizing', 'border-box')
                    .style('font-family', 'Arial, sans-serif')
                    .style('font-size', '14px')
                    .style('line-height', '1.4')
                    .style('word-wrap', 'break-word')
                    .style('overflow-wrap', 'break-word')
                    .style('text-align', 'center')
                    .html(content);
            } else {
                // Render plain text (either no HTML or foreignObject not supported)
                const textContent = containsHtml(content) ? stripHtml(content) : content;
                nodeElement.append('text')
                    .attr('y', nodeHeight / 2)
                    .attr('text-anchor', 'middle')
                    .attr('dominant-baseline', 'middle')
                    .text(textContent);
            }
        });

        node.filter(d => d.data.options && d.data.options.length > 0 && (!d.children || d.children.length === 0))
            .on('dblclick', function(event, d) {
                event.stopPropagation();
                log(`Fetching Q&A for category: ${d.data.label}`);
                renderQA(d.data, d.x, d.y);
            });

        log('Tree rendered with robust global overlap prevention.');
    }

    // Utility: Check if two nodes overlap
    function nodesOverlap(node1, node2, padding = 10) {
        const width1 = node1.data._boxWidth || boxMinWidth;
        const height1 = node1.data._boxHeight || boxHeight;
        const width2 = node2.data._boxWidth || boxMinWidth;
        const height2 = node2.data._boxHeight || boxHeight;
        
        return !(node1.x + width1/2 + padding < node2.x - width2/2 ||
                node1.x - width1/2 > node2.x + width2/2 + padding ||
                node1.y + height1/2 + padding < node2.y - height2/2 ||
                node1.y - height1/2 > node2.y + height2/2 + padding);
    }

    // Utility: Get all nodes at the same level (same depth)
    function getNodesAtLevel(root, level) {
        const nodes = [];
        root.each(node => {
            if (node.depth === level) {
                nodes.push(node);
            }
        });
        return nodes.sort((a, b) => a.x - b.x);
    }

    // Utility: Adjust parent positions to center over their children
    function adjustParentPositions(root) {
        root.eachAfter(node => {
            if (node.children && node.children.length > 0) {
                const children = node.children;
                const minX = Math.min(...children.map(c => c.x));
                const maxX = Math.max(...children.map(c => c.x));
                const centerX = (minX + maxX) / 2;
                
                // Only adjust if the move is significant
                if (Math.abs(node.x - centerX) > 5) {
                    node.x = centerX;
                }
            }
        });
    }

    // Utility: Adjust SVG width for very wide trees
    function adjustSvgWidth(root) {
        const allNodes = root.descendants();
        if (allNodes.length === 0) return;
        
        const minX = d3.min(allNodes, d => d.x - (d.data._boxWidth || boxMinWidth) / 2);
        const maxX = d3.max(allNodes, d => d.x + (d.data._boxWidth || boxMinWidth) / 2);
        const treeWidth = maxX - minX;
        
        // Add padding
        const requiredWidth = treeWidth + 100;
        
        if (requiredWidth > width) {
            // Update SVG width
            svg.attr('width', requiredWidth);
            width = requiredWidth;
            
            // Update container overflow
            if (container) {
                container.style.overflowX = 'auto';
                container.style.overflowY = 'hidden';
            }
            
            log('Adjusted SVG width to:', requiredWidth, 'for tree width:', treeWidth);
        }
    }

    // Expose public API
    window.TreeModule = {
        init: TreeModule.init,
        destroy: TreeModule.destroy,
        addNode: TreeModule.addNode
    };

    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById(config.containerId)) {
            TreeModule.init();
        }
    });

})(window, document, window.d3);