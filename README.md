
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
DELEGATED_USER=your-email@yourdomain.com
# Add other environment variables as needed
```

### 3. Set up Google Service Account for Gmail/Calendar API

#### a. Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project or create a new one.
3. Go to **IAM & Admin > Service Accounts**.
4. Click **Create Service Account**. Give it a name and click **Create and Continue**.
5. Grant the service account the role: **Project > Editor** (or more restrictive as needed).
6. Click **Done**.

#### b. Create and Download Service Account Key
1. In the Service Accounts list, click your new account.
2. Go to the **Keys** tab.
3. Click **Add Key > Create new key**.
4. Choose **JSON** and click **Create**. Download the file as `details.json` and place it in your project root.

#### c. Enable Gmail and Calendar APIs
1. In Google Cloud Console, go to **APIs & Services > Library**.
2. Enable **Gmail API** and **Google Calendar API** for your project.

#### d. Enable Domain-Wide Delegation (for Workspace accounts)
1. In Service Accounts, click your account.
2. Click **Show domain-wide delegation** and enable it.
3. Note the **Client ID** shown.

#### e. Grant API Scopes in Google Admin Console
1. Go to [Google Admin Console](https://admin.google.com/) (requires super admin).
2. Go to **Security > API Controls > Domain-wide Delegation**.
3. Click **Add new** and enter:
   - **Client ID:** (from previous step)
   - **OAuth Scopes:**
     ```
     https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.compose,https://www.googleapis.com/auth/gmail.modify,https://www.googleapis.com/auth/calendar
     ```
4. Save.

#### f. Set DELEGATED_USER
In your `.env`, set `DELEGATED_USER` to the email address of a real user in your Google Workspace domain (not the service account email).

### 4. Install dependencies
```sh
pip install -r requirements.txt
```

### 5. Run the project
Run as per your agent entrypoint (see `manager/agent.py`).

## Usage

- Use the communication agent to send emails or schedule calendar events via Google APIs.
- Use the financial, sales, inventory, and purchase agents for business operations and queries.
- See `examples.md` for sample prompts and usage scenarios for each agent.

## Security & Best Practices

- `.env` and `details.json` are excluded from git via `.gitignore`.
- Never share your `details.json` or `.env` files publicly.
- For Google API integration, ensure your service account has domain-wide delegation enabled and the correct scopes set in the Google Admin Console.

## Example `.env` file

```
DELEGATED_USER=your-email@yourdomain.com
# Add other environment variables as needed
```

## Example Prompts

See `examples.md` for a list of sample questions and commands you can use with each agent.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is for educational and demonstration purposes.
