#!/usr/bin/env bash
# Your first Gemini call: a plain REST request. No SDK, no login, just an API key in a header.
#   Endpoint: .../models/<model>:generateContent      Method: POST      Header: x-goog-api-key
# Usage:  export GEMINI_API_KEY=your_key   then   bash step-1-chat-memory/first_call_curl.sh
MODEL="${GEMINI_MODEL:-gemini-3.8-flash}"
curl -s "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent" \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
        "contents": [ { "role": "user", "parts": [ { "text": "Hi, this is Kumaran" } ] } ]
      }'
echo
