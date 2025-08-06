
# Business Manager ADK

This project is a multi-agent business manager system built with the Agent Development Kit (ADK). It features specialized agents for communication, finance, sales, inventory, and purchase, and integrates with Google APIs for email and calendar automation.

## Features

- Modular multi-agent architecture (ADK)
- Communication agent with Gmail and Google Calendar integration (service account, domain-wide delegation)
- Financial, sales, inventory, and purchase agents with extensible toolsets
- Example prompts and usage scenarios

## File Structure

```
FinalADK/
├── .env                # Environment variables (not committed)
├── .gitignore
├── COMMUNICATION_AGENT_GUIDE.md
├── details.json        # Google service account credentials (not committed)
├── examples.md         # Example prompts for all agents
├── manager/            # Main agent package
│   ├── __init__.py
│   ├── agent.py
│   └── sub_agents/
│       ├── communication/
│       │   ├── agent.py
│       │   ├── config/
│       │   ├── services/
│       │   └── tools/
│       ├── financial/
│       ├── inventory/
│       ├── purchase/
│       └── sales/
│
├── README.md
├── requirements.txt
└── tallydb.db
```


## Getting Started

### 1. Clone the repository
```sh
git clone https://github.com/Praneel7015/business-adk.git
cd business-adk
```

### 2. Create a `.env` file
In the root directory, add:
```env
GOOGLE_API_KEY=putyourkeyhere
GOOGLE_GENAI_USE_VERTEXAI=FALSE
DELEGATED_USER=emailidhere
```

### 3. Set up OAuth Client ID for Gmail/Calendar API

#### a. Create an OAuth Client ID
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project or create a new one.
3. Go to **APIs & Services > Credentials**.
4. Click **Create Credentials > OAuth client ID**.
5. For **Application type**, select **Desktop app**.
6. Give it a name (e.g., "Business Manager Desktop") and click **Create**.
7. Download the credentials file (e.g., `client_secret_XXXX.json`). Rename it to `details.json` and place it in your project root.

#### b. Enable Gmail and Calendar APIs
1. In Google Cloud Console, go to **APIs & Services > Library**.
2. Enable **Gmail API** and **Google Calendar API** for your project.

#### c. First Run: User Consent
1. When you run the agent, a browser window will open for you to log in and authorize Gmail/Calendar access.
2. A `token.pickle` file will be created to store your credentials for future use.

### 4. Setup Virtual Environment
```terminal
python -m venv .venv  
```
```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies
```(.venv) sh
pip install -r requirements.txt
```

### 6. Run Project

```(.venv) sh
adk web
```

Then Click the link shown as follows

```adk
+-----------------------------------------------------------------------------+
| ADK Web Server started                                                      |
|                                                                             |
| For local testing, access at http://localhost:8000.                         |
+-----------------------------------------------------------------------------+
```
or goto [http://localhost:8000.](http://localhost:8000)

## Agent Integration: Sending Emails and Events from Other Agents

- The communication agent exposes tools for sending emails, scheduling calendar events, and creating meeting invitations.
- Other agents (financial, sales, inventory, purchase) can delegate tasks to the communication agent to send emails or create events based on business logic or user requests.
- Example: The sales agent can generate a report and instruct the communication agent to email it to a user.
  
## Usage

- Use the communication agent to send emails or schedule calendar events via Google APIs.
- Use the financial, sales, inventory, and purchase agents for business operations and queries.
- See `examples.md` for sample prompts and usage scenarios for each agent.

## Security & Best Practices

- `.env` and `details.json` are excluded from git via `.gitignore`.
- Never share your `details.json` or `.env` files publicly.
- For Google API integration, ensure your service account has domain-wide delegation enabled and the correct scopes set in the Google Admin Console.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Special Thanks to
Chatgpt (Formatting, Function Fixing and Error Handling)
