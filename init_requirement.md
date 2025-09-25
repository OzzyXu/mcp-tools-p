# Update requirements

1. Change the port number to 11694 for the whole project.
2. I found the IP for the server: 10.126.6.227. I prefer user to connect directly with the IP. Update accordingly.
3. The following are the 7 gpu servers. Please update config and other parts accordingly.
    ```
        ssh python2-gpu1.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu2.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu3.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu4.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu5.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu6.ard-gpu1.hpos.rnd.sas.com
        ssh python2-gpu7.ard-gpu1.hpos.rnd.sas.com
    ```
4. For all the prompt functions, I would like to simplify the usage for users. For example, the function should load the parameters automatically if users didn't specify, like `username = $USER` and in the following example. Update accordingly.
   ```
    from typing import Any, Dict, Optional
    from fastmcp import FastMCP
    app = FastMCP("gpu-mcp")

    @app.prompt("analyze_user_usage")
    def analyze_user_usage(username: str, usage: Optional[Dict[str, Any]] = None) -> str:
        import json
        header = f"You are analyzing GPU usage for user {username}.\n"
        if usage is None:
            body = (
            "If a resource like `gpu://usage/{username}` is present in context, "
            "use it. Otherwise, ask the user to provide usage details."
            )
        else:
            body = "Here is their current GPU usage:\n\n" + json.dumps(usage, indent=2)
        return header + body + (
        "\n\nProvide an analysis including:\n"
        "1) Total resource consumption\n2) Which servers\n3) Efficiency\n4) Recommendations\n"
        )
    ```
5. Update the `servers.json` to `server_config.json`.