#!/bin/bash
# Health check script for all Adajoon services

set -e

echo "🏥 ADAJOON HEALTH CHECK"
echo "======================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="https://backend-production-d32d8.up.railway.app"

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "  ${name}... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_status)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        return 1
    fi
}

# Function to check JSON response
check_json_endpoint() {
    local name=$1
    local url=$2
    local jq_filter=${3:-.}
    
    echo -n "  ${name}... "
    
    if response=$(curl -s "$url" 2>&1); then
        if echo "$response" | jq -e "$jq_filter" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ OK${NC}"
            echo "$response" | jq "$jq_filter" | sed 's/^/    /'
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "    Response: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        return 1
    fi
}

# 1. Backend API
echo "📡 Backend API"
check_endpoint "Health" "$API_URL/api/health"
check_json_endpoint "Categories (has live_count?)" "$API_URL/api/categories" '.[0] | has("live_count")'
check_json_endpoint "Stats" "$API_URL/api/stats" '. | has("channels_count")'

echo ""

# 2. Redis
echo "💾 Redis"
check_json_endpoint "Redis Health" "$API_URL/api/redis/health" '.status == "healthy"'

echo ""

# 3. Database (via validator endpoint)
echo "🗄️  Database"
check_json_endpoint "Validator Status" "$API_URL/api/health/validator" '.channels.total > 0'

echo ""

# 4. Worker Status (check if validation is running)
echo "⚙️  Worker Service"
echo -n "  Checking latest validation timestamp... "
if validated=$(curl -s "$API_URL/api/health/validator" | jq -r '.last_validation_cycle_at' 2>&1); then
    if [ -n "$validated" ] && [ "$validated" != "null" ] && [ "$validated" != "" ]; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "    Last cycle: $validated"
        
        # Check if validation is recent (within last 2 hours)
        current_time=$(date -u +%s)
        validated_time=$(date -u -j -f "%Y-%m-%dT%H:%M:%S" "${validated:0:19}" +%s 2>/dev/null || echo "0")
        age=$((current_time - validated_time))
        
        if [ $age -lt 7200 ]; then
            echo -e "    ${GREEN}Status: Recent (${age}s ago)${NC}"
        else
            echo -e "    ${YELLOW}Status: Stale (${age}s ago)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ UNKNOWN${NC} (No validation data)"
    fi
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""

# 5. Frontend
echo "🎨 Frontend"
check_endpoint "Landing Page" "https://www.adajoon.com"

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo ""

# Check if categories have live_count
if categories=$(curl -s "$API_URL/api/categories" | jq '.[0]' 2>&1); then
    has_live=$(echo "$categories" | jq 'has("live_count")' 2>/dev/null)
    live_value=$(echo "$categories" | jq '.live_count // 0' 2>/dev/null)
    verified_value=$(echo "$categories" | jq '.verified_count // 0' 2>/dev/null)
    
    if [ "$has_live" = "true" ]; then
        if [ "$live_value" = "0" ] && [ "$verified_value" = "0" ]; then
            echo -e "${YELLOW}⚠ Schema updated, but counts still zero${NC}"
            echo "  Reason: Worker hasn't completed first validation cycle yet"
            echo "  Action: Wait 30-60 minutes for worker to validate all channels"
        else
            echo -e "${GREEN}✓ All systems operational${NC}"
            echo "  Live channels: $live_value"
            echo "  Verified channels: $verified_value"
        fi
    else
        echo -e "${RED}✗ Backend deployment incomplete${NC}"
        echo "  Reason: API missing live_count/verified_count fields"
        echo "  Action: Backend deployment still in progress"
    fi
else
    echo -e "${RED}✗ Backend unreachable${NC}"
fi

echo ""
echo "🔗 Useful URLs:"
echo "  Backend:  $API_URL"
echo "  Frontend: https://www.adajoon.com"
echo "  Railway:  https://railway.app/project/b34434ab-c40a-40bc-9d57-4b61d8c1a1a6"
