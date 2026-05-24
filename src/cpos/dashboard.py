import json
from .registry import ContextRegistry
from .context_store import ContextStore

def render_dashboard(registry: ContextRegistry, store: ContextStore, audit_log: list, output_path: str):
    """The 'Task Manager' v3.0. Renders the cognitive state and relationship graph to HTML."""
    
    # 1. Prepare Nodes and Edges for the graph
    nodes = []
    edges = []
    
    for obj in registry.registry.values():
        is_active = obj.id in store.active_contexts
        nodes.append({
            "id": obj.id,
            "label": obj.title[:20],
            "type": obj.type,
            "status": obj.status,
            "active": is_active,
            "heat": obj.access_heat
        })
        
        # Parent-Branch Relationship
        if obj.parent:
            edges.append({"from": obj.parent, "to": obj.id, "type": "branch"})
            
        # Dependencies
        for dep in getattr(obj, 'dependencies', []):
            edges.append({"from": obj.id, "to": dep, "type": "dependency"})

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    html_template = """
    <html>
    <head>
        <title>CPOS Cognitive Dashboard v3.0</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/vis-network.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e14; color: #e1e1e1; padding: 20px; line-height: 1.6; }}
            h1, h2 {{ color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }}
            .container {{ max-width: 1200px; margin: auto; }}
            .layout-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px; }}
            
            #mynetwork {{ width: 100%; height: 500px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #161b22; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #30363d; }}
            th {{ background: #21262d; color: #8b949e; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; }}
            tr:hover {{ background: #1c2128; }}
            
            .badge {{ padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; }}
            .status-active {{ background: #238636; color: white; }}
            .status-stale {{ background: #d29922; color: black; }}
            .status-invalidated {{ background: #da3633; color: white; }}
            .status-loaded {{ color: #00d4ff; font-weight: bold; }}
            
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(0, 212, 255, 0.4); }}
                70% {{ box-shadow: 0 0 0 10px rgba(0, 212, 255, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(0, 212, 255, 0); }}
            }}
            .hot-context {{ border-left: 4px solid #00d4ff; background: rgba(0, 212, 255, 0.05); animation: pulse 2s infinite; }}
            
            .audit-result {{ color: #c9d1d9; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CPOS v10.0 Omega - Cognitive Dashboard</h1>
            
            <div class="layout-grid">
                <div>
                    <h2>🧠 Cognitive Graph (Pointer Relationships)</h2>
                    <div id="mynetwork"></div>
                </div>
                <div>
                    <h2>📜 Live Journal</h2>
                    <div style="max-height: 500px; overflow-y: auto;">
                        <table>
                            <tbody>
                                {audit_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <h2>💾 Memory Map (RAM & Storage)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Pointer ID</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Trust</th>
                        <th>RAM</th>
                    </tr>
                </thead>
                <tbody>
                    {registry_rows}
                </tbody>
            </table>
        </div>

        <script>
            const nodes_data = {nodes_json};
            const edges_data = {edges_json};

            const nodes = new vis.DataSet(nodes_data.map(n => ({{
                id: n.id,
                label: n.label,
                color: n.active ? '#00d4ff' : '#30363d',
                font: {{ color: '#e1e1e1' }},
                shape: 'dot',
                size: 10 + (n.heat * 2)
            }})));

            const edges = new vis.DataSet(edges_data.map(e => ({{
                from: e.from,
                to: e.to,
                arrows: 'to',
                color: e.type === 'branch' ? '#8957e5' : '#238636',
                dashes: e.type === 'dependency'
            }})));

            const container = document.getElementById('mynetwork');
            const data = {{ nodes, edges }};
            const options = {{
                physics: {{ enabled: true, stabilization: true }},
                edges: {{ width: 2 }}
            }};
            new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """
    
    # Generate Registry Rows
    reg_rows = ""
    for obj in registry.registry.values():
        is_loaded = obj.id in store.active_contexts
        ram_status = f"<span class='status-loaded'>RAM</span>" if is_loaded else "<span class='status-disk'>DISK</span>"
        status_label = obj.status.upper()
        reg_rows += f"""
        <tr>
            <td><code>#{obj.id}</code></td>
            <td>{obj.type}</td>
            <td><span class='badge status-{obj.status}'>{status_label}</span></td>
            <td>{obj.trust_score:.2f}</td>
            <td>{ram_status}</td>
        </tr>
        """

    # Generate Audit Rows
    audit_rows = ""
    for entry in reversed(audit_log[-15:]):
        status_color = "#238636" if entry["status"] == "ok" else "#da3633"
        audit_rows += f"""
        <tr>
            <td style="font-size: 0.8em;">
                <code style="color: {status_color}">{entry['action'].upper()}</code><br>
                <small>{entry['target']}</small>
            </td>
        </tr>
        """

    full_html = html_template.format(
        nodes_json=nodes_json,
        edges_json=edges_json,
        registry_rows=reg_rows,
        audit_rows=audit_rows
    )
    
    with open(output_path, "w") as f:
        f.write(full_html)
    print(f"[DASHBOARD] Rendered v3.0 to {output_path}")

def print_terminal_monitor(kernel):
    # (Existing implementation unchanged for CLI simplicity)
    CYAN = "\033[96m"; GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; PURPLE = "\033[95m"; RESET = "\033[0m"; BOLD = "\033[1m"
    corruption = 0.0
    ns_obj = kernel.registry.get("ctx7")
    if ns_obj and ns_obj.data:
        try:
            d = json.loads(ns_obj.data)
            corruption = float(d.get("corruption", 0.0))
        except: pass
    do_glitch = kernel.scheduler.retrieval_policy.visual_glitch_enabled and corruption > 0.4
    def _glitchify(text: str) -> str:
        if not do_glitch: return text
        import random
        chars = list(text)
        for i in range(len(chars)):
            if random.random() < (corruption * 0.2):
                chars[i] = random.choice(["@", "#", "$", "%", "*", "!", "?", "X", "Z", " "])
        return "".join(chars)
    print(f"\n{BOLD}{CYAN}>>> CPOS COGNITIVE MONITOR [NODE: {kernel.node.full_address}] <<<{RESET}")
    print(f"{'-'*60}")
    print(f"{BOLD}[ACTIVE CONTEXTS (RAM)]{RESET}")
    if not kernel.store.active_contexts: print(" (empty)")
    for ctx_id, obj in kernel.store.active_contexts.items():
        heat_bar = "!" * int(min(10, obj.access_heat * 2))
        heat_color = RED if obj.access_heat > 3.0 else YELLOW if obj.access_heat > 1.0 else RESET
        status_color = PURPLE if obj.metadata.get("is_hypothesis") else GREEN
        line = f" #{ctx_id:<12} | {status_color}{obj.status.upper():<10}{RESET} | Heat: {heat_color}{heat_bar:<10}{RESET} | {obj.title}"
        print(_glitchify(line))
    print(f"\n{BOLD}[NEURAL PREDICTION ENGINE]{RESET}")
    history = " -> ".join(kernel.scheduler.cognitive_history[-5:])
    print(_glitchify(f" History: {history}"))
    if kernel.scheduler.cognitive_history:
        last_id = kernel.scheduler.cognitive_history[-1]
        preds = kernel.scheduler.transition_matrix.get(last_id, {})
        if preds:
            top_pred = sorted(preds.items(), key=lambda x: x[1], reverse=True)[0]
            print(_glitchify(f" Next Prediction: {CYAN}{top_pred[0]}{RESET} (Confidence: {top_pred[1]})"))
    mode = kernel.scheduler.retrieval_policy.mode.value.upper()
    metrics_line = f"\n{BOLD}Mode: {GREEN}{mode}{RESET} | Ticks: {kernel.scheduler.tick_count} | Trust Min: {kernel.scheduler.retrieval_policy.minimum_trust_score}"
    if corruption > 0.0: metrics_line += f" | {RED}CORRUPTION: {corruption:.2f}{RESET}"
    print(_glitchify(metrics_line))
    print(f"{'-'*60}\n")
