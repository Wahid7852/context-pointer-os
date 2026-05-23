import json
from .registry import ContextRegistry
from .context_store import ContextStore

def render_dashboard(registry: ContextRegistry, store: ContextStore, audit_log: list, output_path: str):
    """The 'Task Manager'. Renders the system state to HTML."""
    
    html_template = """
    <html>
    <head>
        <title>CPOS Task Manager Dashboard</title>
        <style>
            body {{ font-family: monospace; background: #121212; color: #00ff00; padding: 20px; }}
            h1, h2 {{ border-bottom: 1px solid #00ff00; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #333; padding: 10px; text-align: left; }}
            th {{ background: #1a1a1a; }}
            .heat-bar {{ background: #333; height: 10px; width: 100px; }}
            .heat-fill {{ background: #ff4500; height: 100%; }}
            .status-ok {{ color: #00ff00; }}
            .status-error {{ color: #ff0000; }}
            .ram-item {{ color: #00bfff; }}
        </style>
    </head>
    <body>
        <h1>CPOS v0.9 Dashboard</h1>
        
        <h2>Memory Map (Registry)</h2>
        <table>
            <tr>
                <th>ID</th><th>Type</th><th>Title</th><th>Importance</th><th>Heat</th><th>Status</th>
            </tr>
            {registry_rows}
        </table>

        <h2>Active Contexts (RAM)</h2>
        <table>
            <tr>
                <th>ID</th><th>Title</th><th>Data Preview</th>
            </tr>
            {ram_rows}
        </table>

        <h2>System Audit Log</h2>
        <table>
            <tr>
                <th>Agent</th><th>Instruction</th><th>Action</th><th>Status</th><th>Result</th>
            </tr>
            {audit_rows}
        </table>
    </body>
    </html>
    """
    
    # Generate Registry Rows
    reg_rows = ""
    for obj in registry.registry.values():
        heat_pct = min(100, (obj.access_heat / 10.0) * 100)
        status = "LOADED" if obj.id in store.active_contexts else "DISK"
        reg_rows += f"""
        <tr>
            <td>{obj.id}</td><td>{obj.type}</td><td>{obj.title}</td><td>{obj.importance}</td>
            <td><div class='heat-bar'><div class='heat-fill' style='width: {heat_pct}%'></div></div></td>
            <td>{status}</td>
        </tr>
        """

    # Generate RAM Rows
    ram_rows = ""
    for obj in store.active_contexts.values():
        data_preview = str(obj.data)[:50] + "..." if obj.data else "None"
        ram_rows += f"<tr><td class='ram-item'>{obj.id}</td><td>{obj.title}</td><td>{data_preview}</td></tr>"

    # Generate Audit Rows
    audit_rows = ""
    for entry in reversed(audit_log[-15:]): # Last 15
        status_class = "status-ok" if entry["status"] == "ok" else "status-error"
        audit_rows += f"""
        <tr>
            <td>{entry['agent']}</td><td><code>{entry['instr']}</code></td><td>{entry['action']}</td>
            <td class='{status_class}'>{entry['status']}</td><td>{entry['result']}</td>
        </tr>
        """

    full_html = html_template.format(
        registry_rows=reg_rows,
        ram_rows=ram_rows,
        audit_rows=audit_rows
    )
    
    with open(output_path, "w") as f:
        f.write(full_html)
    print(f"[DASHBOARD] Rendered to {output_path}")
