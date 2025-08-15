from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# In-memory demo store for workflows
# In a real app, replace with a database
workflows = [
    {
        "id": 1,
        "name": "Onboarding Flow",
        "description": "Welcomes new users and collects initial preferences.",
        "cpt_code": "",
        "payer_nuances": [],
    },
    {
        "id": 2,
        "name": "Support Triage",
        "description": "Routes incoming support requests to appropriate queues.",
        "cpt_code": "",
        "payer_nuances": [],
    },
]
next_workflow_id = 3

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/agent-setup')
def agent_setup():
    return render_template('agent_setup.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# API endpoints for workflows
@app.get('/api/workflows')
def list_workflows():
    return jsonify(workflows)


@app.get('/api/workflows/<int:workflow_id>')
def get_workflow(workflow_id: int):
    for wf in workflows:
        if wf["id"] == workflow_id:
            return jsonify(wf)
    return jsonify({"error": "Workflow not found"}), 404


@app.post('/api/workflows')
def create_workflow():
    global next_workflow_id
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    cpt_code = (data.get("cpt_code") or "").strip()
    payer_nuances = data.get("payer_nuances") or []
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    new_wf = {
        "id": next_workflow_id,
        "name": name,
        "description": description,
        "cpt_code": cpt_code,
        "payer_nuances": payer_nuances,
    }
    workflows.append(new_wf)
    next_workflow_id += 1
    return jsonify(new_wf), 201


@app.put('/api/workflows/<int:workflow_id>')
def update_workflow(workflow_id: int):
    data = request.get_json(silent=True) or {}
    for wf in workflows:
        if wf["id"] == workflow_id:
            if "name" in data:
                name = (data.get("name") or "").strip()
                if not name:
                    return jsonify({"error": "'name' is required"}), 400
                wf["name"] = name
            if "description" in data:
                wf["description"] = (data.get("description") or "").strip()
            if "cpt_code" in data:
                wf["cpt_code"] = (data.get("cpt_code") or "").strip()
            if "payer_nuances" in data:
                # expect list of { payer: str, plan_type: 'medicare_advantage'|'commercial', description: str }
                pn = data.get("payer_nuances") or []
                if not isinstance(pn, list):
                    return jsonify({"error": "'payer_nuances' must be a list"}), 400
                wf["payer_nuances"] = pn
            return jsonify(wf)
    return jsonify({"error": "Workflow not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
