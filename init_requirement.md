# Initial Project Requirements

I want to develop a MCP tool with the fastMCP package. The tool would allow users to check the status for a of GPU servers in VSCode Copilot.

Here is a rough descriptions for what the tool does:
1. To be efficient and easy to use, the MCP server will be deployed as the centralized service on the controller of the GPU cluster and transport in the HTTP way.
2. The list of the GPU servers will be provided in a separate file, likely in JSON, MD or TXT format.  
3. In my head, the tool should run a script to SSH to the GPU servers and collect GPU status by command like `nvidia-smi` and perform other actions accordingly.
4. There must be a manual to show how to use the tool.

The tool will be open to my colleagues. Most of them use VSCode under WSL or Remote-SSH.  

The basic functions the tool need to have are:

1. Check the GPU status of all/one machines.
2. Check the GPU usage for a user on all/one machines.
3. Kill the tasks for one user on all/one machines.

A user case I can think for now is to leverage the `.resource` and `.prompt` so the user can ask Copilot 
```plaintext
    User: “Which GPU server is free?”

    Copilot → MCP: fetch gpu://status.

    Copilot → MCP: render prompt summarize_gpu with the resource data.

    LLM generates:

    “GPU02 is mostly idle (10% utilization, 78 GB free memory). Suitable for new jobs.”
```
where
- “Fetch gpu://status”, and they’ll get JSON with GPU stats.
- And
  ```python
  # A prompt: text template with variables
    @app.prompt("summarize_gpu")
    def summarize_gpu():
        """
        Summarize GPU availability into natural language.
        Variables:
        - servers: JSON list of GPU status objects
        """
        return """You are a helpful assistant.
    Here is the current GPU server status:

    {{servers}}

    Write a short summary highlighting which server is most available.
```

Here are some other considerations on efficiency, security and safety like enabling caching to avoid frequently overwriting and 
3) Bound concurrency & add backpressure

Limit concurrent probes to remote boxes with a small semaphore (e.g., 4–8).

Timeout slow probes (e.g., 2–3s) and return the last good snapshot if the cycle overruns.

Add rate limiting per client/IP (simple token bucket) to protect against accidental floods.

Coalesce duplicate in-flight work (if a refresh is running, reuse its result).

4) Fairness & resilience

Per-request deadline (e.g., 5–10s) and cancellation.

Circuit breaker: if sampling fails repeatedly, fall back to cached data and surface a degraded-mode flag.

Health/metrics: log sampling latency, queue depth, timeouts; expose /healthz.

Don't limit yourself. Explore the best implementation based on what I provide above. Check with me first if you need clarification. Let's refine the tool design first.