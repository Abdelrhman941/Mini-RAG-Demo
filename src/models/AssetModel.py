from .BaseDataModel import BaseDataModel
from .db_schemas import Asset
from .enums import DataBaseEnum as DB
from bson import ObjectId


class AssetModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DB.COLLECTION_ASSET_NAME.value]

    # ------------------ Instance creation ------------------
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    # ------------------ Collection initialization ------------------
    async def init_collection(self):
        indexes = Asset.get_indexes()
        for index in indexes:
            await self.collection.create_index(
                index["key"],
                name=index["name"],
                unique=index["unique"]
            )

    # ------------------ Asset operations [CRUD] ------------------
    async def create_asset(self, asset: Asset):
        result = await self.collection.insert_one(asset.model_dump(by_alias=True, exclude_unset=True))
        asset.id = result.inserted_id
        return asset

    # ------------------ Get all assets for a project and asset type ------------------
    async def get_all_project_assets(self, asset_project_id, asset_type: str):
        records = await self.collection.find({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
            "asset_type": asset_type,
        }).to_list(length=None)
        return [Asset(**record) for record in records]

    # ------------------ Get asset by project id and asset name ------------------
    async def get_asset_record(self, asset_project_id, asset_name: str):
        record = await self.collection.find_one({
            "asset_project_id": ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id,
            "asset_name": asset_name,
        })
        return Asset(**record) if record else None
