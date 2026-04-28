# Testing Anti-Patterns

Load this reference when writing or changing tests, adding mocks, or considering test-only production methods.

## Principle

Tests must verify real behavior, not mock behavior.

## Iron Rules

```text
1. Do not test mock existence or mock internals.
2. Do not add production methods that only tests use.
3. Do not mock dependencies you do not understand.
4. Do not create partial mocks when downstream code expects full structures.
```

## Testing Mock Behavior

Bad pattern:

```typescript
render(<Page />);
expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
```

This proves the mock exists, not that `Page` behaves correctly.

Better:

```typescript
render(<Page />);
expect(screen.getByRole('navigation')).toBeInTheDocument();
```

Before asserting on a mock, ask whether the assertion would still matter with the real dependency.

## Test-Only Production Methods

Bad pattern:

```typescript
class Session {
  async destroy() {
    await this.workspace?.destroy();
  }
}
```

If `destroy()` exists only for test cleanup, it does not belong on the production class. Put cleanup in test utilities instead.

## Mocking Without Understanding

Before mocking a method:

1. Identify its real side effects.
2. Check whether the test depends on those side effects.
3. Mock the slow or external boundary, not the high-level behavior under test.

If unsure, run the test against the real dependency first and observe what must be preserved.

## Partial Mocks

Partial mocks hide assumptions.

Bad pattern:

```typescript
const response = {
  status: 'success',
  data: { userId: '123' }
};
```

If real responses include metadata, pagination, headers, or nested fields consumed downstream, include them in the fixture.

Use real examples, API docs, or existing fixtures to mirror the full structure.

## Integration Tests As Afterthought

Testing is part of implementation, not a follow-up phase.

If implementation is "done" but no RED/GREEN evidence exists, the work is not complete. Add the missing regression test before closing the bead.
