"""Tests for Deterministic Verification Layer: Validators, Engine, and Tools."""

import tempfile
from pathlib import Path
import pytest
from alpha.verification.validators import (
    SchemaValidator,
    ArtifactValidator,
    FileExistenceValidator,
    OutputConsistencyValidator,
    ContractValidator
)
from alpha.verification.engine import VerificationEngine
from alpha.verification.tools import (
    VerifySchemaTool,
    VerifyArtifactTool,
    VerifyFileExistenceTool,
    VerifyOutputConsistencyTool
)

def test_schema_validator():
    val = SchemaValidator()
    # Passing schema
    good_data = {"status": "success", "count": 10, "is_valid": True}
    res_pass = val.validate(good_data, {
        "required_fields": ["status", "count"],
        "field_types": {"count": "int", "is_valid": "bool"}
    })
    assert res_pass.passed is True

    # Failing schema (missing field & wrong type)
    bad_data = {"status": "success", "count": "not_an_int"}
    res_fail = val.validate(bad_data, {
        "required_fields": ["status", "missing_token"],
        "field_types": {"count": "int"}
    })
    assert res_fail.passed is False
    assert len(res_fail.errors) == 2

def test_artifact_validator():
    val = ArtifactValidator()

    # Valid Python syntax
    good_code = "def calculate(a, b):\n    return a + b\n"
    res_code = val.validate(good_code, {"check_python_syntax": True, "min_bytes": 10})
    assert res_code.passed is True

    # Bad Python syntax
    bad_code = "def calculate(a, b):\n    return a +"
    res_bad = val.validate(bad_code, {"check_python_syntax": True})
    assert res_bad.passed is False
    assert any("syntax error" in e.lower() for e in res_bad.errors)

def test_file_existence_validator():
    val = FileExistenceValidator()
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write("data")
        real_path = f.name

    try:
        # Pass
        res_pass = val.validate([real_path], {})
        assert res_pass.passed is True

        # Fail
        res_fail = val.validate(["/non/existent/path/alpha.txt"], {})
        assert res_fail.passed is False
        assert "does not exist" in res_fail.errors[0]
    finally:
        Path(real_path).unlink(missing_ok=True)

def test_output_consistency_and_contract():
    consist_val = OutputConsistencyValidator()
    contract_val = ContractValidator()

    # Consistency failure
    err_text = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\nRuntimeError: fail"
    c_res = consist_val.validate(err_text, {})
    assert c_res.passed is False
    assert any("failure marker" in e for e in c_res.errors)

    # Contract evaluation
    target = {"status": 200, "items": [1, 2, 3]}
    res_contract = contract_val.validate(target, {
        "assertions": [
            {"expr": "target['status'] == 200", "description": "Status must be 200"},
            {"expr": "len(target['items']) > 0", "description": "Items non-empty"}
        ]
    })
    assert res_contract.passed is True

def test_verification_engine_and_tools():
    engine = VerificationEngine()
    schema_tool = VerifySchemaTool(engine)
    artifact_tool = VerifyArtifactTool(engine)
    consist_tool = VerifyOutputConsistencyTool(engine)

    # Schema tool
    s_res = schema_tool.run(
        data={"user": "alpha", "role": "admin"},
        required_fields=["user", "role"]
    )
    assert s_res["status"] == "verified"

    # Artifact tool
    a_res = artifact_tool.run(
        content="val = 42\n",
        check_python_syntax=True,
        min_bytes=5
    )
    assert a_res["status"] == "verified"

    # Consistency tool
    c_res = consist_tool.run(
        output_text="Completed task with clean execution.",
        required_keywords=["clean"]
    )
    assert c_res["status"] == "verified"
