# Tower Mock API Server

This mock API server provides fake endpoints for testing Tower CLI integration tests without requiring a real Tower API server.

## Common Issues After API Schema Changes

### Problem: Integration tests fail with "UnknownDescribeSessionValue" errors

This typically happens after regenerating the Tower API client from an updated OpenAPI specification. The mock API responses no longer match the expected schema.

**Symptoms:**
```
DEBUG MCP: Session creation failed: UnknownDescribeSessionValue { value: Object {...} }
```

**Root Cause:**
The mock API is returning JSON that doesn't match the Rust structs generated from the OpenAPI spec. This usually means:
1. Required fields are missing from the mock response
2. Field names have changed 
3. Field types have changed
4. New required fields were added to the API

### Debugging Steps

1. **Check the API models**: Look at the generated Rust structs in `crates/tower-api/src/models/` to see what fields are required:
   ```bash
   # Check the User model
   cat crates/tower-api/src/models/user.rs
   
   # Check the Session model  
   cat crates/tower-api/src/models/session.rs
   
   # Check other related models
   ls crates/tower-api/src/models/
   ```

2. **Compare with mock response**: Look at the mock API response in `main.py` and ensure all required fields are present with correct types.

3. **Test the session endpoint directly**:
   ```bash
   # Start the mock server
   cd tests/mock-api-server && ./run.sh
   
   # Test the endpoint
   curl -H "Authorization: Bearer mock_jwt_token" http://127.0.0.1:8000/v1/session | jq
   ```

4. **Run a single test with debug output**:
   ```bash
   cd tests/integration
   TOWER_MOCK_API_URL=http://127.0.0.1:8000 uv run behave features/mcp_app_management.feature -n "Run simple application successfully locally" --no-capture
   ```

### Updating the Mock API

When the API schema changes, update the responses in `main.py`:

1. **For session endpoint**: Update the `/v1/session` response to match the new `User`, `Session`, etc. models
2. **For other endpoints**: Update responses to match new field requirements
3. **Add missing fields**: Check the Rust structs for new required fields and add them with sensible mock values
4. **Remove deprecated fields**: Remove fields that are no longer in the API (but be careful - some might be optional)

### Example Fix

If the `User` model gains a new required field `department: String`, update the mock response:

```python
"user": {
    # ... existing fields ...
    "department": "Engineering",  # New required field
}
```

## Testing Your Changes

After updating the mock API:

1. Restart the mock server: `cd tests/mock-api-server && ./run.sh`
2. Run the integration tests: `cd tests/integration && TOWER_MOCK_API_URL=http://127.0.0.1:8000 uv run behave features/`
3. Ensure all tests pass

## Files to Update

When the API schema changes, you may need to update:

- `main.py` - The mock API responses
- This README - If new debugging steps are needed
- The integration tests themselves (in `features/`) - If test expectations change