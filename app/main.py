from fastapi import FastAPI, Request

app = FastAPI(title="Autonomous Living Knowledge Engine MVP")

@app.post("/webhooks/github")
async def github_webhook(request: Request):
    # TODO: Verify HMAC signature
    # TODO: Enqueue event task
    payload = await request.json()
    return {"status": "ok", "message": "GitHub event received"}

@app.post("/webhooks/slack")
async def slack_webhook(request: Request):
    # TODO: Verify signature
    # TODO: Enqueue event task
    payload = await request.json()
    return {"status": "ok", "message": "Slack event received"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
