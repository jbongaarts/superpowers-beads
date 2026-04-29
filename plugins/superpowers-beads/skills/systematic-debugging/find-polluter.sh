#!/usr/bin/env bash
# Bisection script to find which test creates unwanted files/state
# Usage:   ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: ./find-polluter.sh '.git' 'src/**/*.test.ts'
#
# The runner defaults to 'npm test' for Node/JS projects. Override
# TEST_CMD for other ecosystems — the matched test path is appended
# as the final argument.
#
# Examples:
#   TEST_CMD='pytest'        ./find-polluter.sh '.cache' 'tests/**/*.py'
#   TEST_CMD='go test'       ./find-polluter.sh '.tmp'   './pkg/**/*_test.go'
#   TEST_CMD='cargo test --' ./find-polluter.sh 'target/wip' 'tests/**/*.rs'

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <file_to_check> <test_pattern>"
  echo "Example: $0 '.git' 'src/**/*.test.ts'"
  echo ""
  echo "Override the test runner via TEST_CMD (default: 'npm test'):"
  echo "  TEST_CMD='pytest' $0 '.cache' 'tests/**/*.py'"
  exit 1
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"
TEST_CMD="${TEST_CMD:-npm test}"

echo "🔍 Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo "Test runner:  $TEST_CMD"
echo ""

# Get list of test files
TEST_FILES=$(find . -path "$TEST_PATTERN" | sort)
TOTAL=$(echo "$TEST_FILES" | wc -l | tr -d ' ')

echo "Found $TOTAL test files"
echo ""

COUNT=0
for TEST_FILE in $TEST_FILES; do
  COUNT=$((COUNT + 1))

  # Skip if pollution already exists
  if [ -e "$POLLUTION_CHECK" ]; then
    echo "⚠️  Pollution already exists before test $COUNT/$TOTAL"
    echo "   Skipping: $TEST_FILE"
    continue
  fi

  echo "[$COUNT/$TOTAL] Testing: $TEST_FILE"

  # Run the test
  # shellcheck disable=SC2086 # intentional word-splitting to honor TEST_CMD
  $TEST_CMD "$TEST_FILE" > /dev/null 2>&1 || true

  # Check if pollution appeared
  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "🎯 FOUND POLLUTER!"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    echo ""
    echo "Pollution details:"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  $TEST_CMD $TEST_FILE    # Run just this test"
    echo "  cat $TEST_FILE          # Review test code"
    exit 1
  fi
done

echo ""
echo "✅ No polluter found - all tests clean!"
exit 0
