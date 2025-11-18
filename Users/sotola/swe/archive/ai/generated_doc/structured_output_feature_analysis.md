# Claude Code ENABLE_STRUCTURED_OUTPUT Feature Analysis

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]

## Overview

The `ENABLE_STRUCTURED_OUTPUT` feature allows Claude Code to return responses in a structured JSON format that conforms to a user-provided JSON schema. This is useful for non-interactive sessions where programmatic consumption of Claude's output is needed.

---

## Feature Toggle

### Helper Function (Line 474533-474537)

```javascript
function jt2(A) {
  return Boolean(
    process.env.ENABLE_STRUCTURED_OUTPUT && A.isNonInteractiveSession,
  );
}
```

**Requirements:**
- Environment variable `ENABLE_STRUCTURED_OUTPUT` must be set
- Session must be non-interactive (`isNonInteractiveSession: true`)

---

## Tool Definition

### Base Tool Object (E21) - Lines 474546-474596

```javascript
E21 = {
  isMcp: false,
  isEnabled() { return true; },
  isConcurrencySafe() { return true; },
  isReadOnly() { return true; },
  isDestructive() { return false; },
  isOpenWorld() { return false; },

  name: "StructuredOutput",

  async description() {
    return "Return structured output in the requested format";
  },

  async prompt() {
    return "Use this tool to return your final response in the requested structured format. You MUST call this tool exactly once at the end of your response to provide the structured output.";
  },

  inputSchema: r2I,   // y.object({}).passthrough() - accepts any properties
  outputSchema: o2I,  // y.string().describe("Structured output tool result")

  async call(A) {
    return {
      data: "Structured output provided successfully",
      structured_output: A,
    };
  },

  async checkPermissions(A) {
    return { behavior: "allow", updatedInput: A };
  },

  renderToolUseMessage(A) {
    let B = Object.keys(A);
    if (B.length === 0) return null;
    if (B.length <= 3)
      return B.map((Q) => `${Q}: ${JSON.stringify(A[Q])}`).join(", ");
    return `${B.length} fields: ${B.slice(0, 3).join(", ")}…`;
  },

  userFacingName: () => "StructuredOutput",

  renderToolUseRejectedMessage() {
    return "Structured output rejected";
  },

  renderToolUseErrorMessage() {
    return "Structured output error";
  },

  renderToolUseProgressMessage() {
    return null;
  }
}
```

---

## Schemas

### Input Schema (r2I) - Line 474544

```javascript
r2I = y.object({}).passthrough()
```

This is a Zod schema that accepts an empty object with any additional properties. This allows the user-provided schema to define the actual structure.

### Output Schema (o2I) - Line 474545

```javascript
o2I = y.string().describe("Structured output tool result")
```

The tool returns a string describing the result.

---

## User-Provided Schema Integration

### CLI Flag (Line 496427-496430)

```javascript
.addOption(
  new YW("--output-schema <schema>", "JSON schema for structured output.")
    .argParser(String)
    .hideHelp(),
)
```

**Usage:**
```bash
claude --output-schema '{"type":"object","properties":{"name":{"type":"string"},"age":{"type":"number"}},"required":["name","age"]}' "Generate user data"
```

### Schema Parsing and Validation (Lines 496850-496891)

```javascript
// Check if feature is enabled and schema is provided
if (jt2({ isNonInteractiveSession: WA }) && J.outputSchema)
  HA = JSON.parse(J.outputSchema);

if (HA) {
  try {
    // Create AJV validator instance
    let rA = new _Q9.default({ allErrors: true });

    // Validate the schema itself
    if (!rA.validateSchema(HA))
      throw Error(`Invalid JSON Schema: ${rA.errorsText(rA.errors)}`);

    // Compile the schema for runtime validation
    let y1 = rA.compile(HA);

    // Create modified tool with custom validation
    let e1 = {
      ...E21,
      inputJSONSchema: HA,  // Store user's schema

      async call(A0) {
        // Validate output against user's schema
        if (!y1(A0)) {
          let a0 = y1.errors
            ?.map((IB) => `${IB.dataPath || "root"}: ${IB.message}`)
            .join(", ");
          throw Error(`Output does not match required schema: ${a0}`);
        }

        // Fire success telemetry
        GA("tengu_structured_output_success", {
          schema_property_count: Object.keys(HA.properties || {}).length,
          output_property_count: Object.keys(A0).length,
        });

        return {
          data: "Structured output provided successfully",
          structured_output: A0,
        };
      },
    };

    // Add modified tool to tool list
    UA = [...UA, e1];

    // Fire enabled telemetry
    GA("tengu_structured_output_enabled", {
      schema_property_count: Object.keys(HA.properties || {}).length,
      has_required_fields: Boolean(HA.required),
    });

  } catch (rA) {
    // Fire failure telemetry
    GA("tengu_structured_output_failure", {
      error: rA instanceof Error ? rA.message : String(rA),
    });
    QA(rA instanceof Error ? rA : Error(String(rA)), xW0);
  }
}
```

---

## Rendering Helpers

### Tool Use Message Rendering (Lines 474581-474586)

```javascript
renderToolUseMessage(A) {
  let B = Object.keys(A);
  if (B.length === 0) return null;
  if (B.length <= 3)
    return B.map((Q) => `${Q}: ${JSON.stringify(A[Q])}`).join(", ");
  return `${B.length} fields: ${B.slice(0, 3).join(", ")}…`;
}
```

**Examples:**

**Empty object:**
```javascript
renderToolUseMessage({})  // → null
```

**1-3 fields:**
```javascript
renderToolUseMessage({ name: "John", age: 30 })
// → "name: \"John\", age: 30"
```

**More than 3 fields:**
```javascript
renderToolUseMessage({ name: "John", age: 30, city: "NYC", country: "USA" })
// → "4 fields: name, age, city…"
```

### Error Messages (Lines 474589-474596)

```javascript
renderToolUseRejectedMessage() {
  return "Structured output rejected";
}

renderToolUseErrorMessage() {
  return "Structured output error";
}

renderToolUseProgressMessage() {
  return null;  // No progress message
}
```

---

## Permission Plumbing

### Permission Check (Lines 474578-474580)

```javascript
async checkPermissions(A) {
  return { behavior: "allow", updatedInput: A };
}
```

**Behavior:**
- Always allows the tool use without prompting
- Returns the input unchanged
- No special permissions required

### Tool Properties (Lines 474547-474562)

```javascript
isMcp: false,                    // Not an MCP tool
isEnabled() { return true; },    // Always enabled
isConcurrencySafe() { return true; },  // Can run concurrently
isReadOnly() { return true; },   // Read-only operation
isDestructive() { return false; }, // Non-destructive
isOpenWorld() { return false; }  // Doesn't access external resources
```

---

## Telemetry Events

### 1. Feature Enabled (Line 496882-496885)

```javascript
GA("tengu_structured_output_enabled", {
  schema_property_count: Object.keys(HA.properties || {}).length,
  has_required_fields: Boolean(HA.required),
});
```

**Fires when:** Schema is successfully validated and feature is enabled

**Properties:**
- `schema_property_count`: Number of properties in the schema
- `has_required_fields`: Whether schema has required fields

### 2. Success (Lines 496869-496873)

```javascript
GA("tengu_structured_output_success", {
  schema_property_count: Object.keys(HA.properties || {}).length,
  output_property_count: Object.keys(A0).length,
});
```

**Fires when:** Claude successfully calls the tool with valid output

**Properties:**
- `schema_property_count`: Number of properties in the schema
- `output_property_count`: Number of properties in the actual output

### 3. Failure (Lines 496887-496889)

```javascript
GA("tengu_structured_output_failure", {
  error: rA instanceof Error ? rA.message : String(rA),
});
```

**Fires when:** Schema validation or setup fails

**Properties:**
- `error`: Error message describing the failure

### 4. Max Retries Exceeded (Lines 493709-493716)

```javascript
yield {
  type: "result",
  subtype: "error_max_structured_output_retries",
  duration_ms: Date.now() - i,
  duration_api_ms: u$(),
  is_error: false,
  num_turns: OA,
  session_id: E0(),
  // ...
}
```

**Fires when:** Claude fails to provide valid output after MAX_STRUCTURED_OUTPUT_RETRIES attempts

---

## Retry Logic

### Configuration (Line 493707)

```javascript
let L0 = parseInt(process.env.MAX_STRUCTURED_OUTPUT_RETRIES || "5", 10);
```

**Default:** 5 retries

**Customization:**
```bash
export MAX_STRUCTURED_OUTPUT_RETRIES=10
```

### Retry Counter (Line 493708)

```javascript
if (Ae2(C, gy, L0) >= L0) {
  // Session aborts with error_max_structured_output_retries
}
```

The `Ae2()` function counts how many times the StructuredOutput tool (`gy`) has been called in the conversation (`C`).

---

## API Schema Conversion (Lines 322738-322741)

```javascript
input_schema:
  "inputJSONSchema" in A && A.inputJSONSchema
    ? A.inputJSONSchema
    : Rd(A.inputSchema),
```

When sending the tool definition to the API:
- If `inputJSONSchema` exists (user-provided schema), use it
- Otherwise, convert the Zod schema to JSON Schema using `Rd()`

---

## Complete Example Usage

### 1. Simple User Schema

**Command:**
```bash
export ENABLE_STRUCTURED_OUTPUT=1

claude --output-schema '{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "summary": {"type": "string"},
    "tags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["title", "summary"]
}' "Summarize the React documentation"
```

**Claude's behavior:**
1. Receives the StructuredOutput tool with the user's schema
2. Reads/analyzes the React documentation
3. Calls `StructuredOutput` with:
   ```json
   {
     "title": "React Documentation Overview",
     "summary": "React is a JavaScript library for building user interfaces...",
     "tags": ["react", "javascript", "ui", "components"]
   }
   ```
4. Tool validates the output against schema
5. Returns structured_output to the session

### 2. Complex Nested Schema

**Schema:**
```json
{
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "number", "minimum": 0}
      },
      "required": ["name", "email"]
    },
    "metadata": {
      "type": "object",
      "properties": {
        "created_at": {"type": "string", "format": "date-time"},
        "source": {"type": "string"}
      }
    }
  },
  "required": ["user"]
}
```

**Validation:**
- AJV validates schema structure
- AJV compiles for runtime validation
- Each StructuredOutput call is validated
- Errors show specific path and message: `"user/email: should match format \"email\""`

### 3. Error Handling

**Invalid Schema:**
```bash
claude --output-schema '{"type": "invalid"}' "test"
```

**Result:**
- Telemetry: `tengu_structured_output_failure`
- Error: "Invalid JSON Schema: data.type should be equal to one of the allowed values"
- Session continues without structured output

**Invalid Output:**
- If Claude calls StructuredOutput with data that doesn't match
- Error thrown: "Output does not match required schema: name: is required"
- Claude can retry (up to MAX_STRUCTURED_OUTPUT_RETRIES)

---

## Summary

The `ENABLE_STRUCTURED_OUTPUT` feature provides:

1. **Toggle Helper**: Environment-based feature flag with non-interactive check
2. **Tool Definition**: Complete StructuredOutput tool with prompt, schemas, and rendering
3. **Schema Validation**: AJV-based validation of both schema and output
4. **Permission Plumbing**: Auto-allow with safe, read-only properties
5. **Telemetry**: Three events tracking enable, success, and failure
6. **Retry Logic**: Configurable max retries with session abort
7. **Rendering Helpers**: Smart field display (show all if ≤3, otherwise summarize)

This enables programmatic use of Claude Code in non-interactive contexts where structured, validated JSON output is required.

---

[Created by Claude: 6e83e738-42ed-4003-9b75-abfd2c86cd9d]
