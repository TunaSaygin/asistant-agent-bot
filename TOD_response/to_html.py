import json

# Load JSON data
with open('./TOD_response/2024-07-18.json', 'r') as file:
    data = json.load(file)
# Start HTML structure
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dialogue Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; }
        .sidebar { width: 200px; background-color: #f0f0f0; padding: 10px; border-right: 1px solid #ddd; }
        .sidebar h2 { font-size: 18px; margin-top: 0; }
        .dialogue-list { list-style-type: none; padding: 0; }
        .dialogue-list li { margin-bottom: 10px; }
        .dialogue-list a { text-decoration: none; color: blue; cursor: pointer; }
        .content { flex: 1; padding: 20px; }
        .dialogue { margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .dialogue-title { cursor: pointer; color: blue; text-decoration: underline; font-size: 18px; }
        .dialogue-content { display: none; margin-top: 10px; }
        .response { margin-left: 20px; }
        .response strong { display: block; margin-top: 5px; }
        h1 { text-align: center; }
        h3 { color: #333; }
        .whatsapp-message { background-color: #dcf8c6; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 60%; }
        .system-message { background-color: #ffffff; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 60%; }
        .user-message { text-align: right; }
    </style>
    <script>
        function toggleDialogueContent(id) {
            var content = document.getElementById(id);
            if (content.style.display === 'none') {
                content.style.display = 'block';
            } else {
                content.style.display = 'none';
            }
        }

        function showDialogue(id) {
            var dialogues = document.getElementsByClassName('dialogue-content');
            for (var i = 0; i < dialogues.length; i++) {
                dialogues[i].style.display = 'none';
            }
            document.getElementById(id).style.display = 'block';
        }
    </script>
</head>
<body>
    <div class="sidebar">
        <h2>Dialogues</h2>
        <ul class="dialogue-list">
"""

# Generate the sidebar menu for each dialogue
for i, dialogue in enumerate(data):
    dialogue_id = f"dialogue_{i}"
    html_content += f'<li><a onclick="showDialogue(\'{dialogue_id}\')">Dialogue {i + 1}</a></li>'

html_content += """
        </ul>
    </div>
    <div class="content">
        <h1>Dialogue Viewer</h1>
"""

# Generate HTML content for each dialogue
for i, dialogue in enumerate(data):
    dialogue_id = f"dialogue_{i}"
    html_content += f"""
    <div class="dialogue-content" id="{dialogue_id}" style="display: none;">
        <h3>History</h3>
    """
    history_lines = dialogue['history'].split("', ")
    for line in history_lines:
        line = line.replace("\'", "")
        if 'User:' in line:
            html_content += f'''<div class="whatsapp-message user-message">{line}</div>'''
        else:
            html_content += f'''<div class="whatsapp-message system-message">{line}</div>'''
    html_content += """
        <h3>GT Responses</h3>
    """
    for gt in dialogue['GT']:
        html_content += f"""
            <div class="response">
                <strong>Belief State:</strong> {json.dumps(gt['belief_state'], indent=2)}
                <strong>Text:</strong> {gt['text']}
            </div>
        """
    html_content += """
        <h3>GPT Responses</h3>
    """
    for gpt in dialogue['GPT']:
        html_content += f"""
            <div class="response">
                <strong>Belief State:</strong> {json.dumps(gpt['belief_state'], indent=2)}
                <strong>Text:</strong> {gpt['text']}
            </div>
        """
    html_content += """
        <h3>LLAMA Responses</h3>
    """
    for llama in dialogue['LLAMA']:
        html_content += f"""
            <div class="response">
                <strong>Belief State:</strong> {json.dumps(llama['belief_state'], indent=2)}
                <strong>Text:</strong> {llama['text']}
            </div>
        """
    html_content += """
    </div>
    """

# End HTML structure
html_content += """
    </div>
</body>
</html>
"""

# Write HTML content to file
with open('./TOD_response/dial_viewer.html', 'w') as file:
    file.write(html_content)

print("HTML file 'dialogue_viewer.html' has been generated.")
