SuperAsk.AI - Demo 1 code (Team AO3)
====================================

Where the code is
-----------------
The code is NOT copied into this folder. SuperAsk is a Next.js application,
and Next.js requires its source folders to sit at the repository root. A copy
here would go out of date, so this file points to the real location instead:

    https://github.com/Monunhh/Super-ask

    app/          web pages and API routes (/api/ask, /api/feedback,
                  /api/health, /api/telegram/webhook)
    components/   React user interface (chat, landing page, site shell)
    lib/          answer engine, retrieval, Khmer language processing,
                  model providers, Telegram bot, crawler, audit logging
    data/         knowledge base, curated answers, glossary, source registry
    scripts/      command-line tools (evaluation, quality checks, crawler)

Most source files start with a comment block explaining their purpose, and the
requirement IDs it implements (FR-xx, NFR-xx) refer to the project reports.

How to run the code
-------------------
Requirements: Node.js 22 or newer, npm, and an internet connection for
the first install.

1. Clone the repository and open its root folder (where package.json is):

       git clone https://github.com/Monunhh/Super-ask.git
       cd Super-ask

2. Install dependencies:

       npm install

3. Create a local settings file. No API key is needed: with none, the app
   uses its built-in extractive answer mode, which quotes the official source.

       cp .env.example .env.local          (macOS / Linux)
       Copy-Item .env.example .env.local   (Windows PowerShell)

4. Start the app and open http://localhost:3000 in a browser:

       npm run dev

5. Optional production build:

       npm run build
       npm start

The deployed prototype is at https://superask.vercel.app and the Telegram bot
is @superask168_bot.
