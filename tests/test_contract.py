
from contracts.utility_contract import UtilityContract, EntryPoint, Dependency

def test_round_trip():
    spec = UtilityContract(
        name="demo",
        version="0.0.1",
        language="python",
        description="demo utility",
        entrypoints=[
            EntryPoint(
                name="hello",
                description="say hi",
                parameters_schema={},
                return_schema={}
            )
        ],
        deps=[Dependency(package="requests", version=">=2")],
        tests=["tests/test_demo.py"]
    )
    assert spec.dict()["name"] == "demo"
