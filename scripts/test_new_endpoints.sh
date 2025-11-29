#!/bin/bash

#############################################################################
# Test Script for New Health and Stats Endpoints
#
# Usage:
#   ./scripts/test_new_endpoints.sh
#
# Tests the newly added health and statistics endpoints
#############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8010/api/v1"

echo -e "${BLUE}=== Testing New UNS-Kobetsu Endpoints ===${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2

    echo -e "${YELLOW}Testing: $description${NC}"
    echo "Endpoint: $endpoint"

    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ Success (HTTP $response)${NC}"
        echo "Response:"
        curl -s "$endpoint" | python3 -m json.tool | head -20
    else
        echo -e "${RED}✗ Failed (HTTP $response)${NC}"
    fi
    echo ""
}

# Test health endpoints
echo -e "${BLUE}Health Endpoints:${NC}"
echo ""

test_endpoint "$API_URL/health/basic" "Basic Health Check"
test_endpoint "$API_URL/health/detailed" "Detailed Health Check"
test_endpoint "$API_URL/health/ready" "Readiness Check"
test_endpoint "$API_URL/health/live" "Liveness Check"

# Test statistics endpoints
echo -e "${BLUE}Statistics Endpoints:${NC}"
echo ""

test_endpoint "$API_URL/stats/system" "System Statistics"
test_endpoint "$API_URL/stats/app" "Application Statistics"
test_endpoint "$API_URL/stats/database" "Database Statistics"
test_endpoint "$API_URL/stats/usage?days=7" "Usage Statistics (7 days)"

echo -e "${GREEN}=== Testing Complete ===${NC}"