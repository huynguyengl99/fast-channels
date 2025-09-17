#!/bin/bash

# Script to run the Redis Sentinel test inside Docker
#
# Usage:
#   ./run_test.sh              # Full build and teardown
#   ./run_test.sh --cache      # Keep compose up, skip build, mount source
#   ./run_test.sh -c           # Short form of --cache
#   ./run_test.sh --ci         # CI mode (no docker-compose, uses external services)

set +e

# Parse command line arguments
CACHE_MODE=false
CI_MODE=false

# Auto-detect CI environment
if [[ -n "${CI}" || -n "${GITHUB_ACTIONS}" ]]; then
    CI_MODE=true
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --cache|-c)
            CACHE_MODE=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --cache, -c   Use cache mode (keep compose up, skip build, mount source)"
            echo "  --ci          CI mode (no docker-compose, uses external services)"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Cache mode benefits:"
            echo "  - Keeps Redis Sentinel cluster running"
            echo "  - Skips Docker image rebuild"
            echo "  - Mounts source code for instant updates"
            echo ""
            echo "CI mode:"
            echo "  - Skips docker-compose setup"
            echo "  - Expects Redis and Sentinel to be available externally"
            echo "  - Uses environment variables for connection"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Function to cleanup on script exit (only if not in cache mode and not in CI mode)
cleanup() {
    if [ "$CACHE_MODE" = false ] && [ "$CI_MODE" = false ]; then
        echo "🧹 Cleaning up Docker containers..."
        cd "$SCRIPT_DIR"
        docker-compose down > /dev/null 2>&1
    fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT

cd "$SCRIPT_DIR"

if [ "$CI_MODE" = false ]; then
    # Start Redis Sentinel services (if not already running)
    echo "🚀 Starting Redis Sentinel cluster..."
    docker-compose up -d

    # Wait for services to be ready
    echo "⏳ Waiting for Redis Sentinel to be ready..."
    sleep 1
else
    echo "🤖 Running in CI mode - expecting external Redis + Sentinel services"
fi

if [ "$CI_MODE" = true ]; then
    echo "🧪 Running tests in CI mode..."
    cd "$PROJECT_ROOT"

    # Run tests directly
    pytest tests_extra/redis_sentinel/tests

    TEST_EXIT_CODE=$?

elif [ "$CACHE_MODE" = true ]; then
    echo "💨 Running in cache mode (mounting source, skipping build)..."

    # Run tests with mounted source code using existing image
    # The Dockerfile copies redis_sentinel files to /app root, so mount there
    cd "$PROJECT_ROOT"
    docker run --rm \
      --network redis_sentinel_redis-net \
      -v "$PROJECT_ROOT/fast_channels:/app/fast_channels" \
      -v "$SCRIPT_DIR/tests:/app/tests" \
      fast-channels-sentinel-test

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ Tests passed! Redis Sentinel cluster is still running for next test."
    else
        echo "❌ Tests failed! Redis Sentinel cluster is still running for debugging."
    fi

else
    echo "🐳 Building Docker image..."

    # Build the Docker image from project root with redis_sentinel context
    cd "$PROJECT_ROOT"
    docker build -f tests_extra/redis_sentinel/Dockerfile -t fast-channels-sentinel-test .

    # Run the test container and connect it to the Redis network
    echo "🧪 Running tests in built container..."
    docker run --rm \
      --network redis_sentinel_redis-net \
      fast-channels-sentinel-test

    TEST_EXIT_CODE=$?
fi

# Exit with the same code as the tests
exit $TEST_EXIT_CODE
