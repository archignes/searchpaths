
# You can find your profile path by opening Chrome or Brave and going to
# chrome://version/ or brave://version/
# Then look for the "Profile Path" heading.
#
# Credit: Randy Lauen (maker of History Trends Unlimited (HTU)) points this out at
# https://sites.google.com/view/history-trends-unlimited/faq#h.p_rBVxOKWmdGsJ

# Examples here are for Chrome, Brave, and the export from the HTU extension.
HISTORY_DATABASE_PATHS = {
    "Chrome": "/Users/dsg/Library/Application Support/Google/Chrome/Default",
    "Brave": "/Users/dsg/Library/Application Support/BraveSoftware/Brave-Browser/Profile 6",
    "HTUexport": "external_data/htu_analyze_20240424_133319.tsv"
}

# This can be used to access the HTU history database without manual export.
# It will be synced as of the last time the extension was used OR the browser was restarted.
HTU_PROFILE_PATH = "/Users/dsg/Library/Application Support/BraveSoftware/Brave-Browser/Profile 6"

# Filtering and Processing Configurations

SKIP_DOMAINS = [
    "http://localhost",
    "https://instantdomains.com",
    "*.vercel.app"
]

SITE_SEARCH_DOMAINS = [
    "https://searchjunct.com",
    "https://instantdomains.com",
    "https://danielsgriffin.com",
    "https://twitter.com",
    "https://www.tiktok.com",
    "https://github.com"
]

# These are search systems that may not always (or ever) have query strings indicated in search pages.
LOGGABLE_SEARCH_SYSTEMS = [
    "https://www.findera.ai/",
    "https://you.com/",
    "https://chat.openai.com/",
    "https://copilot.microsoft.com/",
    "https://andisearch.com/",
    "https://www.perplexity.ai/search",
    "https://komo.ai/",
    "https://coral.cohere.com/",
    "https://app.tavily.com/playground",
    "https://huggingface.co/chat/",
    "https://search.lepton.run/",
    "https://morphic.sh/",
    "https://gemini.google.com/app",
    "https://claude.ai/chat/"
]

CHAT_BASED_SEARCH_COMPLEMENTS = [
    "https://claude.ai/chat/",
    "https://chat.openai.com/",
    "https://gemini.google.com/app"
]
