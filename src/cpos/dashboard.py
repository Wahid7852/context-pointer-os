import json
from .registry import ContextRegistry
from .context_store import ContextStore

def render_dashboard(registry: ContextRegistry, store: ContextStore, audit_log: list, output_path: str):
    """The 'Task Manager' v2.0. Renders the Spec v0.1-v0.3 system state to HTML."""
    
    html_template = """
    <html>
    <head>
        <title>CPOS Cognitive Dashboard v2.0</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e14; color: #e1e1e1; padding: 20px; line-height: 1.6; }}
            h1, h2 {{ color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; }}
            .container {{ max-width: 1200px; margin: auto; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #161b22; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #30363d; }}
            th {{ background: #21262d; color: #8b949e; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; }}
            tr:hover {{ background: #1c2128; }}
            
            /* Status Badges */
            .badge {{ padding: 4px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; }}
            .status-active {{ background: #238636; color: white; }}
            .status-stale {{ background: #d29922; color: black; }}
            .status-invalidated {{ background: #da3633; color: white; }}
            .status-hyp {{ background: #8957e5; color: white; }}
            .status-loaded {{ color: #00d4ff; font-weight: bold; }}
            .status-disk {{ color: #8b949e; }}
            
            /* Trust & Heat Bars */
            .meter-bg {{ background: #30363d; height: 8px; width: 100px; border-radius: 4px; display: inline-block; vertical-align: middle; margin-right: 8px; }}
            .meter-fill {{ height: 100%; border-radius: 4px; }}
            .trust-fill {{ background: #238636; }}
            .heat-fill {{ background: #ff4500; }}
            
            .sensitivity-public {{ color: #238636; }}
            .sensitivity-internal {{ color: #00d4ff; }}
            .sensitivity-private {{ color: #d29922; }}
            .sensitivity-restricted {{ color: #da3633; font-weight: bold; }}

            code {{ background: #0d1117; padding: 2px 4px; border-radius: 4px; color: #ff7b72; }}
            .audit-result {{ color: #c9d1d9; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CPOS v2.6 Cognitive Dashboard</h1>
            
            <h2>🧠 Memory Map (Pointer Registry)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Pointer ID</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Trust Score</th>
                        <th>Heat Index</th>
                        <th>Sensitivity</th>
                        <th>RAM</th>
                    </tr>
                </thead>
                <tbody>
                    {registry_rows}
                </tbody>
            </table>

            <h2>💾 Active Contexts (RAM)</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title / Summary</th>
                        <th>Data Preview</th>
                    </tr>
                </thead>
                <tbody>
                    {ram_rows}
                </tbody>
            </table>

            <h2>📜 System Kernel Journal</h2>
            <table>
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Instruction</th>
                        <th>Action</th>
                        <th>Result / Audit Log</th>
                    </tr>
                </thead>
                <tbody>
                    {audit_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    # Generate Registry Rows
    reg_rows = ""
    for obj in registry.registry.values():
        heat_pct = min(100, (obj.access_heat / 10.0) * 100)
        trust_pct = min(100, obj.trust_score * 100)
        is_loaded = obj.id in store.active_contexts
        ram_status = f"<span class='status-loaded'>LOADED</span>" if is_loaded else "<span class='status-disk'>DISK</span>"
        
        status_class = f"status-{obj.status}"
        status_label = obj.status.upper()
        if obj.metadata.get("is_hypothesis"):
            status_class = "status-hyp"
            status_label = "HYPOTHESIS"

        reg_rows += f"""
        <tr>
            <td><code>#{obj.id}</code></td>
            <td>{obj.type}</td>
            <td><span class='badge {status_class}'>{status_label}</span></td>
            <td>
                <div class='meter-bg'><div class='meter-fill trust-fill' style='width: {trust_pct}%'></div></div>
                {obj.trust_score:.2f}
            </td>
            <td>
                <div class='meter-bg'><div class='meter-fill heat-fill' style='width: {heat_pct}%'></div></div>
            </td>
            <td><span class='sensitivity-{obj.sensitivity_level}'>{obj.sensitivity_level.upper()}</span></td>
            <td>{ram_status}</td>
        </tr>
        """

    # Generate RAM Rows
    ram_rows = ""
    for obj in store.active_contexts.values():
        data_preview = str(obj.data)[:80] + "..." if obj.data else "None"
        ram_rows += f"""
        <tr>
            <td><code>#{obj.id}</code></td>
            <td><strong>{obj.title}</strong><br><small>{obj.summary}</small></td>
            <td class='audit-result'>{data_preview}</td>
        </tr>
        """

    # Generate Audit Rows
    audit_rows = ""
    for entry in reversed(audit_log[-20:]): # Show last 20
        status_color = "#238636" if entry["status"] == "ok" else "#da3633"
        if entry["status"] == "awaiting_approval": status_color = "#d29922"
        
        audit_rows += f"""
        <tr>
            <td><strong>{entry['agent']}</strong><br><small>PID: {entry.get('pid', 0)}</small></td>
            <td><code>{entry['instr']}</code></td>
            <td style='color: {status_color}'>{entry['action'].upper()}</td>
            <td class='audit-result'>{entry['result']}</td>
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
