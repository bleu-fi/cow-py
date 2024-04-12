import httpx
import json
from typing import Any, Dict, List
from cow_py.common.config import CowEnv, SupportedChainId
from .generated.model import (
    AppDataObject,
    OrderQuoteSide,
    OrderQuoteValidity,
    OrderQuoteValidity1,
    Trade,
    Order,
    TotalSurplus,
    NativePriceResponse,
    SolverCompetitionResponse,
    OrderQuoteRequest,
    OrderQuoteResponse,
    OrderCreation,
    UID,
    Address,
    TransactionHash,
    AppDataHash,
    OrderCancellation,
)

from cow_py.order_book.api_config import (
    DEFAULT_BACKOFF_OPTIONS,
    DEFAULT_LIMITER_OPTIONS,
    APIConfigFactory,
    JsonResponseAdapter,
    RequestBuilder,
    RequestStrategy,
    backoff_decorator,
    rate_limit_decorator,
)


Context = dict[str, str]


class OrderBookApi:
    def __init__(self, context: Context = {}):
        self.config = APIConfigFactory.get_config(
            context.get("env", CowEnv.PROD),
            context.get("chain_id", SupportedChainId.MAINNET),
        )

    @backoff_decorator(DEFAULT_BACKOFF_OPTIONS)
    @rate_limit_decorator(DEFAULT_LIMITER_OPTIONS)
    async def _fetch(
        self, path, method: str = "GET", context_override: Context = {}, **kwargs
    ):
        context = {**self.config.get_context(), **context_override}
        url = context.get("base_url") + path
        async with httpx.AsyncClient() as client:
            builder = RequestBuilder(
                RequestStrategy(),
                JsonResponseAdapter(),
            )
            print(method)
            return await builder.execute(client, url, method, **kwargs)

    def _get_context_with_override(
        self, context_override: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if context_override is None:
            context_override = {}
        return {**self.context, **context_override}

    async def get_version(self, context_override: Dict[str, Any] = None) -> str:
        return await self._fetch(
            path="/api/v1/version", context_override=context_override
        )

    async def get_trades_by_owner(
        self, owner: Address, context_override: Dict[str, Any] = None
    ) -> List[Trade]:
        response = await self._fetch(
            path="/api/v1/trades",
            params={"owner": owner},
            context_override=context_override,
        )
        return [Trade(**trade) for trade in response]

    async def get_trades_by_order_uid(
        self, order_uid: UID, context_override: Dict[str, Any] = None
    ) -> List[Trade]:
        response = await self._fetch(
            path="/api/v1/trades",
            params={"order_uid": order_uid},
            context_override=context_override,
        )
        return [Trade(**trade) for trade in response]

    async def get_orders_by_owner(
        self,
        owner: Address,
        limit: int = 1000,
        offset: int = 0,
        context_override: Dict[str, Any] = None,
    ) -> List[Order]:
        return [
            Order(**order)
            for order in await self._fetch(
                path=f"/api/v1/account/{owner}/orders",
                params={"limit": limit, "offset": offset},
                context_override=context_override,
            )
        ]

    async def get_order_by_uid(
        self, order_uid: UID, context_override: Dict[str, Any] = None
    ) -> Order:
        response = await self._fetch(
            path=f"/api/v1/orders/{order_uid}",
            context_override=context_override,
        )
        return Order(**response)

    def get_order_link(
        self, order_uid: UID, context_override: Dict[str, Any] = None
    ) -> str:
        return (
            self.get_api_url(self._get_context_with_override(context_override))
            + f"/api/v1/orders/{order_uid.root}"
        )

    async def get_tx_orders(
        self, tx_hash: TransactionHash, context_override: Dict[str, Any] = None
    ) -> List[Order]:
        response = await self._fetch(
            path=f"/api/v1/transactions/{tx_hash}/orders",
            context_override=context_override,
        )
        return [Order(**order) for order in response]

    async def get_native_price(
        self, tokenAddress: Address, context_override: Dict[str, Any] = None
    ) -> NativePriceResponse:
        response = await self._fetch(
            path=f"/api/v1/token/{tokenAddress}/native_price",
            context_override=context_override,
        )
        return NativePriceResponse(**response)

    async def get_total_surplus(
        self, user: Address, context_override: Dict[str, Any] = None
    ) -> TotalSurplus:
        response = await self._fetch(
            path=f"/api/v1/users/{user}/total_surplus",
            context_override=context_override,
        )
        return TotalSurplus(**response)

    async def get_app_data(
        self, app_data_hash: AppDataHash, context_override: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        return await self._fetch(
            path=f"/api/v1/app_data/{app_data_hash}",
            context_override=context_override,
        )

    async def get_solver_competition(
        self, action_id: int = "latest", context_override: Dict[str, Any] = None
    ) -> SolverCompetitionResponse:
        response = await self._fetch(
            path=f"/api/v1/solver_competition/{action_id}",
            context_override=context_override,
        )
        return SolverCompetitionResponse(**response)

    async def get_solver_competition_by_tx_hash(
        self, tx_hash: TransactionHash, context_override: Dict[str, Any] = None
    ) -> SolverCompetitionResponse:
        response = await self._fetch(
            path=f"/api/v1/solver_competition/by_tx_hash/{tx_hash}",
            context_override=context_override,
        )
        return SolverCompetitionResponse(**response)

    async def post_quote(
        self,
        request: OrderQuoteRequest,
        side: OrderQuoteSide,
        validity: OrderQuoteValidity = OrderQuoteValidity1(),
        context_override: Dict[str, Any] = None,
    ) -> OrderQuoteResponse:
        response = await self._fetch(
            path="/api/v1/quote",
            json={
                **request.dict(by_alias=True),
                # side object need to be converted to json first to avoid on kind type
                **json.loads(side.json()),
                **validity.dict(),
            },
            context_override=context_override,
            method="POST",
        )
        return OrderQuoteResponse(**response)

    async def post_order(
        self, order: OrderCreation, context_override: Dict[str, Any] = None
    ):
        response = await self._fetch(
            path="/api/v1/orders",
            json=json.loads(order.json(by_alias=True)),
            context_override=context_override,
            method="POST",
        )
        return UID(response)

    async def delete_order(
        self,
        orders_cancelation: OrderCancellation,
        context_override: Dict[str, Any] = None,
    ):
        response = await self._fetch(
            path="/api/v1/orders",
            json=orders_cancelation.json(),
            context_override=context_override,
            method="DELETE",
        )
        return UID(response)

    async def put_app_data(
        self,
        app_data: AppDataObject,
        app_data_hash: str = None,
        context_override: Dict[str, Any] = None,
    ) -> AppDataHash:
        app_data_hash_url = app_data_hash if app_data_hash else ""
        response = await self._fetch(
            path=f"/api/v1/app_data/{app_data_hash_url}",
            json=app_data.json(),
            context_override=context_override,
            method="PUT",
        )
        return AppDataHash(response)