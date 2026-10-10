"""设备（facility）领域模型。"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from hfyuwo.models.base import RuoYiModel


class Facility(RuoYiModel):
    facility_id: Optional[int] = Field(None, alias="facilityId")
    facility_number: Optional[str] = Field(None, alias="facilityNumber")
    facility_name: Optional[str] = Field(None, alias="facilityName")
    facility_type: Optional[str] = Field(None, alias="facilityType")
    facility_connection_status: Optional[str] = Field(
        None, alias="facilityConnectionStatus"
    )
    facility_machine_status: Optional[str] = Field(None, alias="facilityMachineStatus")
    facility_count: Optional[int] = Field(None, alias="facilityCount")
    facility_address: Optional[str] = Field(None, alias="facilityAddress")
    operator_id: Optional[int] = Field(None, alias="operatorId")
    operator_name: Optional[str] = Field(None, alias="operatorName")
    operator_phone: Optional[str] = Field(None, alias="operatorPhone")
    uploaddata_time: Optional[str] = Field(None, alias="uploaddataTime")
    expiration_time: Optional[str] = Field(None, alias="expirationTime")

    @property
    def machine_id(self) -> str:
        if self.facility_id is not None:
            return str(self.facility_id)
        if self.facility_number:
            return self.facility_number
        return ""

    @property
    def machine_name(self) -> str | None:
        return self.facility_name


class FacilityDetail(Facility):
    """GET /vending/facility/{id} 详情，在列表字段基础上扩展。"""

    create_time: Optional[str] = Field(None, alias="createTime")
    update_time: Optional[str] = Field(None, alias="updateTime")
    facility_area: Optional[str] = Field(None, alias="facilityArea")
    facility_renew_status: Optional[str] = Field(None, alias="facilityRenewStatus")
    facility_signal_intensity: Optional[str] = Field(
        None, alias="facilitySignalIntensity"
    )
    facility_version: Optional[str] = Field(None, alias="facilityVersion")
    facility_status: Optional[str] = Field(None, alias="facilityStatus")
    facility_lon: Optional[str] = Field(None, alias="facilityLon")
    facility_lat: Optional[str] = Field(None, alias="facilityLat")
    facility_tel: Optional[str] = Field(None, alias="facilityTel")
    type_id: Optional[int] = Field(None, alias="typeId")
    facility_replenish_time: Optional[str] = Field(None, alias="facilityReplenishTime")
    freight_track_count: Optional[int] = Field(None, alias="freightTrackCount")
    facility_lack_status: Optional[str] = Field(None, alias="facilityLackStatus")
    facility_notes: Optional[str] = Field(None, alias="facilityNotes")
    auto_refund: Optional[str] = Field(None, alias="autoRefund")
    device_password: Optional[str] = Field(None, alias="password")
    test_time: Optional[str] = Field(None, alias="testTime")
    is_screen: Optional[str] = Field(None, alias="isScreen")
    pay_resource: Optional[int] = Field(None, alias="payResource")
    discount_status: Optional[int] = Field(None, alias="discountStatus")
    imei: Optional[str] = None
    iccid: Optional[str] = None
    iccid_expiration_time: Optional[str] = Field(None, alias="iccidExpirationTime")
    goods_num: Optional[int] = Field(None, alias="goodsNum")
    is_light: Optional[int] = Field(None, alias="isLight")
    seconds: Optional[int] = None
    get_track_info: Optional[int] = Field(None, alias="getTrackInfo")
    buy_type: Optional[int] = Field(None, alias="buyType")
    is_ava: Optional[int] = Field(None, alias="isAva")
