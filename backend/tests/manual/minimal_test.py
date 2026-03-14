import asyncio


async def main():
    print("1. Importing ExecutionContext...")
    from app.contracts.trace import ExecutionContext

    print("2. Creating context...")
    ctx = ExecutionContext.create(request_source="test")

    print("3. Importing engine...")
    from app.engines.identity_subscription.engine import IdentitySubscriptionEngine

    print("4. Creating engine instance...")
    engine = IdentitySubscriptionEngine()

    print("5. Calling engine.run()...")
    result = await engine.run(ctx)

    print(f"6. Result: success={result.success}")


if __name__ == "__main__":
    asyncio.run(main())
