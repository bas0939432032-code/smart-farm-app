"""Smart Farm Management System - Full Stack OOP Project Standard."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import io
import unittest

import pandas as pd
import streamlit as st


# ============================= Domain and contracts =============================
class ValidationError(ValueError):
    """ข้อมูลนำเข้าไม่ผ่านกฎธุรกิจ"""


class User(ABC):
    def __init__(self, user_id: int, username: str, email: str, password: str, role: str) -> None:
        if user_id <= 0 or not username.strip() or "@" not in email:
            raise ValidationError("ข้อมูลผู้ใช้ไม่ถูกต้อง")
        if len(password) < 4:
            raise ValidationError("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
        self._user_id = user_id
        self._username = username.strip()
        self._email = email.strip().lower()
        self._password_hash = hashlib.sha256(password.encode()).hexdigest()
        self._role = role
        self._is_active = True

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValidationError("ชื่อผู้ใช้ต้องไม่ว่าง")
        self._username = value.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValidationError("อีเมลไม่ถูกต้อง")
        self._email = value.strip().lower()

    @property
    def role(self) -> str:
        return self._role

    @property
    def is_active(self) -> bool:
        return self._is_active

    def deactivate(self) -> None:
        self._is_active = False

    def activate(self) -> None:
        self._is_active = True

    @abstractmethod
    def get_permissions(self) -> List[str]:
        raise NotImplementedError

    def authenticate(self, password: str) -> bool:
        return self._is_active and self._password_hash == hashlib.sha256(password.encode()).hexdigest()


class Farmer(User):
    def __init__(self, user_id: int, username: str, email: str, password: str, farm_license: str = "SMART-2026") -> None:
        super().__init__(user_id, username, email, password, "เกษตรกร")
        self._farm_license = farm_license
        self._farms: List[Farm] = []

    @property
    def farm_license(self) -> str:
        return self._farm_license

    @property
    def farms(self) -> List[Farm]:
        return list(self._farms)

    def manage_farm(self, farm: Farm) -> None:
        if farm not in self._farms:
            self._farms.append(farm)

    def get_permissions(self) -> List[str]:
        return ["ดู Dashboard", "จัดการฟาร์ม", "จัดการอุปกรณ์", "คำนวณการรดน้ำ", "บันทึกผลผลิต"]


class Admin(User):
    def __init__(self, user_id: int, username: str, email: str, password: str, admin_level: int = 1) -> None:
        super().__init__(user_id, username, email, password, "ผู้ดูแลระบบ")
        if admin_level < 1:
            raise ValidationError("ระดับผู้ดูแลระบบไม่ถูกต้อง")
        self._admin_level = admin_level

    @property
    def admin_level(self) -> int:
        return self._admin_level

    def get_permissions(self) -> List[str]:
        return ["ดู Dashboard", "จัดการฟาร์ม", "จัดการอุปกรณ์", "คำนวณการรดน้ำ", "จัดการผู้ใช้งาน", "บันทึกผลผลิต", "ดู API", "รันการทดสอบ"]


class SuperAdmin(Admin):
    def __init__(self, user_id: int, username: str, email: str, password: str) -> None:
        User.__init__(self, user_id, username, email, password, "ซูเปอร์แอดมิน")
        self._admin_level = 99

    def get_permissions(self) -> List[str]:
        return ["สิทธิ์ทั้งหมด", "จัดการผู้ใช้งาน", "กำหนดสิทธิ์", "ลบผู้ใช้งาน", "ดู API", "รันการทดสอบ"]


class Device(ABC):
    def __init__(self, device_id: str, name: str, location: str) -> None:
        if not device_id.strip() or not name.strip() or not location.strip():
            raise ValidationError("รหัส ชื่อ และตำแหน่งอุปกรณ์ต้องไม่ว่าง")
        self._device_id, self._name, self._location = device_id.strip(), name.strip(), location.strip()
        self._is_active = True

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def location(self) -> str:
        return self._location

    @property
    def is_active(self) -> bool:
        return self._is_active

    def set_active(self, active: bool) -> None:
        self._is_active = bool(active)

    @abstractmethod
    def execute_action(self) -> str:
        raise NotImplementedError


class SensorDevice(Device):
    def __init__(self, device_id: str, name: str, location: str, sensor_type: str) -> None:
        super().__init__(device_id, name, location)
        self._sensor_type = sensor_type.strip() or (_ for _ in ()).throw(ValidationError("ประเภทเซนเซอร์ต้องไม่ว่าง"))

    @property
    def sensor_type(self) -> str:
        return self._sensor_type

    def execute_action(self) -> str:
        return f"อ่านค่าจาก {self._name} ({self._sensor_type}) สำเร็จ"


class ActuatorDevice(Device):
    def __init__(self, device_id: str, name: str, location: str, capacity_lpm: float) -> None:
        super().__init__(device_id, name, location)
        if capacity_lpm <= 0:
            raise ValidationError("อัตราการไหลต้องมากกว่า 0")
        self._capacity_lpm = float(capacity_lpm)
        self._state = "ปิด"

    @property
    def capacity_lpm(self) -> float:
        return self._capacity_lpm

    @property
    def state(self) -> str:
        return self._state

    def execute_action(self) -> str:
        self._state = "เปิด"
        return f"เปิดระบบรดน้ำ {self._name} อัตราไหล {self._capacity_lpm:g} ลิตร/นาที"

    def switch(self, state: str) -> str:
        if state not in {"เปิด", "ปิด"}:
            raise ValidationError("สถานะต้องเป็น เปิด หรือ ปิด")
        self._state = state
        return f"{self._name} เปลี่ยนสถานะเป็น {state}"


class Crop:
    def __init__(self, crop_id: int, name: str, ideal_moisture: float, growth_days: int) -> None:
        if not name.strip() or not 0 <= ideal_moisture <= 100 or growth_days <= 0:
            raise ValidationError("ข้อมูลพืชไม่ถูกต้อง")
        self._crop_id, self._name = crop_id, name.strip()
        self._ideal_moisture, self._growth_days = ideal_moisture, growth_days
        self._status = "กำลังปลูก"

    @property
    def crop_id(self) -> int:
        return self._crop_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def ideal_moisture(self) -> float:
        return self._ideal_moisture

    @property
    def growth_days(self) -> int:
        return self._growth_days

    @property
    def status(self) -> str:
        return self._status

    def harvest(self) -> None:
        self._status = "เก็บเกี่ยวแล้ว"


class Plot:
    def __init__(self, plot_id: int, name: str, area_sqm: float) -> None:
        if area_sqm <= 0 or not name.strip():
            raise ValidationError("ชื่อแปลงต้องไม่ว่างและพื้นที่ต้องมากกว่า 0")
        self._plot_id, self._name, self._area_sqm = plot_id, name.strip(), float(area_sqm)
        self._crops: List[Crop] = []

    @property
    def plot_id(self) -> int:
        return self._plot_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def area_sqm(self) -> float:
        return self._area_sqm

    @property
    def crops(self) -> List[Crop]:
        return list(self._crops)

    @property
    def current_crop(self) -> Optional[Crop]:
        return next((crop for crop in self._crops if crop.status == "กำลังปลูก"), None)

    def plant_crop(self, crop: Crop) -> None:
        if self.current_crop:
            raise ValidationError("แปลงนี้มีพืชที่กำลังปลูกอยู่แล้ว")
        self._crops.append(crop)


class Farm:
    def __init__(self, farm_id: int, name: str, owner: Farmer, location: str = "ไม่ระบุ") -> None:
        if not name.strip():
            raise ValidationError("ชื่อฟาร์มต้องไม่ว่าง")
        self._farm_id, self._name, self._owner, self._location = farm_id, name.strip(), owner, location
        self._plots: List[Plot] = []  # Composition: Farm owns Plot lifecycle.

    @property
    def farm_id(self) -> int:
        return self._farm_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def owner(self) -> Farmer:
        return self._owner

    @property
    def location(self) -> str:
        return self._location

    @property
    def plots(self) -> List[Plot]:
        return list(self._plots)

    def add_plot(self, name: str, area_sqm: float) -> Plot:
        if any(plot.name.lower() == name.strip().lower() for plot in self._plots):
            raise ValidationError("ชื่อแปลงซ้ำกันในฟาร์ม")
        plot = Plot(len(self._plots) + 1, name, area_sqm)
        self._plots.append(plot)
        return plot


class SensorData:
    def __init__(self, data_id: int, device_id: str, moisture: float, temp: float) -> None:
        if not 0 <= moisture <= 100 or temp < -50 or temp > 80:
            raise ValidationError("ค่าความชื้นหรืออุณหภูมิอยู่นอกช่วงที่รองรับ")
        self._data_id, self._device_id = data_id, device_id
        self._moisture, self._temp, self._timestamp = moisture, temp, datetime.now()

    @property
    def data_id(self) -> int:
        return self._data_id

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def moisture(self) -> float:
        return self._moisture

    @property
    def temp(self) -> float:
        return self._temp

    @property
    def timestamp(self) -> str:
        return self._timestamp.strftime("%Y-%m-%d %H:%M:%S")


class IrrigationTask:
    def __init__(self, task_id: int, plot_name: str, water_amount: float, status: str = "รอดำเนินการ") -> None:
        if water_amount <= 0:
            raise ValidationError("ปริมาณน้ำต้องมากกว่า 0")
        self._task_id, self._plot_name = task_id, plot_name
        self._water_amount, self._status = float(water_amount), status

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def plot_name(self) -> str:
        return self._plot_name

    @property
    def water_amount(self) -> float:
        return self._water_amount

    @property
    def status(self) -> str:
        return self._status

    def complete(self) -> None:
        self._status = "เสร็จสิ้น"


class HarvestRecord:
    def __init__(self, record_id: int, crop_name: str, yield_kg: float, revenue: float, harvest_date: Optional[str] = None) -> None:
        if not crop_name.strip() or yield_kg <= 0 or revenue < 0:
            raise ValidationError("ชื่อพืชต้องไม่ว่าง ผลผลิตต้องมากกว่า 0 และรายได้ห้ามติดลบ")
        self._record_id, self._crop_name = record_id, crop_name.strip()
        self._yield_kg, self._revenue = float(yield_kg), float(revenue)
        self._harvest_date = harvest_date or date.today().isoformat()

    @property
    def record_id(self) -> int:
        return self._record_id

    @property
    def crop_name(self) -> str:
        return self._crop_name

    @property
    def yield_kg(self) -> float:
        return self._yield_kg

    @property
    def revenue(self) -> float:
        return self._revenue

    @property
    def harvest_date(self) -> str:
        return self._harvest_date


class Notification:
    def __init__(self, notification_id: int, message: str, severity: str = "แจ้งเตือน") -> None:
        self._notification_id, self._message, self._severity = notification_id, message, severity
        self._created_at, self._is_read = datetime.now(), False

    @property
    def notification_id(self) -> int:
        return self._notification_id

    @property
    def message(self) -> str:
        return self._message

    @property
    def severity(self) -> str:
        return self._severity

    @property
    def created_at(self) -> str:
        return self._created_at.strftime("%H:%M:%S")

    @property
    def is_read(self) -> bool:
        return self._is_read

    def mark_read(self) -> None:
        self._is_read = True


class IIrrigationStrategy(ABC):
    @abstractmethod
    def calculate_water(self, current_moisture: float, target_moisture: float) -> float:
        raise NotImplementedError


class ISensorObserver(ABC):
    @abstractmethod
    def update(self, data: SensorData) -> Optional[Notification]:
        raise NotImplementedError


class LowMoistureObserver(ISensorObserver):
    def __init__(self, threshold: float = 30.0) -> None:
        self._threshold = threshold

    def update(self, data: SensorData) -> Optional[Notification]:
        if data.moisture < self._threshold:
            return Notification(0, f"ความชื้นต่ำ: อุปกรณ์ {data.device_id} มีค่า {data.moisture:.1f}% ต่ำกว่าเกณฑ์ {self._threshold:.0f}%", "เร่งด่วน")
        return None


class MoistureBasedStrategy(IIrrigationStrategy):
    def calculate_water(self, current_moisture: float, target_moisture: float) -> float:
        if not 0 <= current_moisture <= 100 or not 0 <= target_moisture <= 100:
            raise ValidationError("ค่าความชื้นต้องอยู่ระหว่าง 0-100%")
        return round(max(0, target_moisture - current_moisture) * 2.5, 2)


class TimerBasedStrategy(IIrrigationStrategy):
    def calculate_water(self, current_moisture: float, target_moisture: float) -> float:
        return 15.0


# ============================= Patterns and services =============================
class DeviceFactory:
    @staticmethod
    def create_device(dtype: str, dev_id: str, name: str, location: str, parameter: str) -> Device:
        if dtype.lower() == "sensor":
            return SensorDevice(dev_id, name, location, parameter)
        if dtype.lower() == "actuator":
            try:
                return ActuatorDevice(dev_id, name, location, float(parameter))
            except (TypeError, ValueError) as error:
                raise ValidationError("พารามิเตอร์ Actuator ต้องเป็นตัวเลข") from error
        raise ValidationError("ประเภทอุปกรณ์ต้องเป็น Sensor หรือ Actuator")


class NotificationCenter:
    def __init__(self) -> None:
        self._observers: List[ISensorObserver] = []

    def subscribe(self, observer: ISensorObserver) -> None:
        self._observers.append(observer)

    def notify(self, data: SensorData) -> List[Notification]:
        notices: List[Notification] = []
        for observer in self._observers:
            notice = observer.update(data)
            if notice:
                notices.append(notice)
        return notices


class UserRepository:
    """Repository สำหรับ CRUD ผู้ใช้งานและการกำหนดสิทธิ์"""

    ROLE_TYPES = {"เกษตรกร": Farmer, "ผู้ดูแลระบบ": Admin, "ซูเปอร์แอดมิน": SuperAdmin}

    def __init__(self) -> None:
        self._users: List[User] = []
        self._next_id = 1

    def add(self, username: str, email: str, password: str, role: str) -> User:
        if role not in self.ROLE_TYPES:
            raise ValidationError("บทบาทผู้ใช้งานไม่ถูกต้อง")
        if any(user.email == email.strip().lower() for user in self._users):
            raise ValidationError("อีเมลนี้มีอยู่ในระบบแล้ว")
        user_class = self.ROLE_TYPES[role]
        if user_class is Farmer:
            user = Farmer(self._next_id, username, email, password)
        elif user_class is Admin:
            user = Admin(self._next_id, username, email, password)
        else:
            user = SuperAdmin(self._next_id, username, email, password)
        self._users.append(user)
        self._next_id += 1
        return user

    def add_existing(self, user: User) -> User:
        self._users.append(user)
        self._next_id = max(self._next_id, user.user_id + 1)
        return user

    def all(self) -> List[User]:
        return list(self._users)

    def get(self, user_id: int) -> Optional[User]:
        return next((user for user in self._users if user.user_id == user_id), None)

    def find(self, keyword: str) -> List[User]:
        term = keyword.strip().lower()
        return [user for user in self._users if term in user.username.lower() or term in user.email]

    def update(self, user_id: int, username: str, email: str, role: str) -> User:
        current = self.get(user_id)
        if current is None:
            raise ValidationError("ไม่พบผู้ใช้งานที่เลือก")
        normalized_email = email.strip().lower()
        if any(user.user_id != user_id and user.email == normalized_email for user in self._users):
            raise ValidationError("อีเมลนี้มีอยู่ในระบบแล้ว")
        current.username = username
        current.email = normalized_email
        if current.role != role:
            replacement = self._replace_role(current, role)
            self._users[self._users.index(current)] = replacement
            current = replacement
        return current

    def _replace_role(self, current: User, role: str) -> User:
        if role not in self.ROLE_TYPES:
            raise ValidationError("บทบาทผู้ใช้งานไม่ถูกต้อง")
        user_class = self.ROLE_TYPES[role]
        if user_class is Farmer:
            replacement = Farmer(current.user_id, current.username, "user@example.com", "temp")
        elif user_class is Admin:
            replacement = Admin(current.user_id, current.username, "user@example.com", "temp")
        else:
            replacement = SuperAdmin(current.user_id, current.username, "user@example.com", "temp")
        replacement._email = current.email
        replacement._password_hash = current._password_hash
        replacement._is_active = current.is_active
        return replacement

    def deactivate(self, user_id: int) -> User:
        user = self.get(user_id)
        if user is None:
            raise ValidationError("ไม่พบผู้ใช้งานที่เลือก")
        user.deactivate()
        return user

    def activate(self, user_id: int) -> User:
        user = self.get(user_id)
        if user is None:
            raise ValidationError("ไม่พบผู้ใช้งานที่เลือก")
        user.activate()
        return user

    def delete(self, user_id: int) -> None:
        user = self.get(user_id)
        if user is None:
            raise ValidationError("ไม่พบผู้ใช้งานที่เลือก")
        self._users.remove(user)


class FarmRepository:
    TABLES = ["users", "roles", "farms", "plots", "crops", "devices", "sensor_data", "irrigation_tasks", "harvest_records", "notifications"]

    def __init__(self, seed: bool = True) -> None:
        self._data: Dict[str, List[Any]] = {table: [] for table in self.TABLES}
        self._counters: Dict[str, int] = {table: 0 for table in self.TABLES}
        if seed:
            self.seed()

    def next_id(self, table: str) -> int:
        self._counters[table] += 1
        return self._counters[table]

    def add(self, table: str, value: Any) -> Any:
        self._data[table].append(value)
        return value

    def all(self, table: str) -> List[Any]:
        return list(self._data[table])

    def seed(self) -> None:
        farmer = Farmer(self.next_id("users"), "วีรชัย ห้อยเหม", "veerachai@example.com", "SMART-2026")
        admin = Admin(self.next_id("users"), "ผู้ดูแลระบบ", "admin@example.com", "admin1234")
        super_admin = SuperAdmin(self.next_id("users"), "ซูเปอร์แอดมิน", "superadmin@example.com", "super1234")
        self.add("users", farmer)
        self.add("users", admin)
        self.add("users", super_admin)
        self.add("roles", {"role": "เกษตรกร", "permissions": "ดูแลฟาร์ม, บันทึกผลผลิต"})
        self.add("roles", {"role": "ผู้ดูแลระบบ", "permissions": "จัดการระบบทั้งหมด"})
        farm = Farm(self.next_id("farms"), "สมาร์ทฟาร์ม ธนบุรี", farmer, "กรุงเทพมหานคร")
        farmer.manage_farm(farm)
        self.add("farms", farm)
        plot_a = farm.add_plot("แปลงผักสลัด A1", 120)
        plot_b = farm.add_plot("แปลงสตอเบอร์รี่ B1", 150)
        self.add("plots", plot_a)
        self.add("plots", plot_b)
        crop_a = Crop(self.next_id("crops"), "ผักสลัด Green Oak", 65, 45)
        crop_b = Crop(self.next_id("crops"), "สตอเบอร์รี่ พันธุ์ 80", 75, 90)
        plot_a.plant_crop(crop_a)
        plot_b.plant_crop(crop_b)
        self.add("crops", crop_a)
        self.add("crops", crop_b)
        self.add("devices", SensorDevice("S-101", "เซนเซอร์ความชื้น A1", "แปลง A1", "ความชื้นในดิน"))
        self.add("devices", ActuatorDevice("V-101", "วาล์วน้ำ A1", "แปลง A1", 30.5))
        self.add("sensor_data", SensorData(self.next_id("sensor_data"), "S-101", 24, 28.5))
        self.add("sensor_data", SensorData(self.next_id("sensor_data"), "S-102", 68.5, 27))
        self.add("irrigation_tasks", IrrigationTask(self.next_id("irrigation_tasks"), "แปลงผักสลัด A1", 100))
        self.add("harvest_records", HarvestRecord(self.next_id("harvest_records"), "ผักสลัด Green Oak", 150, 12000, "2026-09-10"))
        self.add("harvest_records", HarvestRecord(self.next_id("harvest_records"), "สตอเบอร์รี่ พันธุ์ 80", 85.5, 25650, "2026-09-18"))
        notice = LowMoistureObserver().update(self.all("sensor_data")[0])
        if notice:
            notice._notification_id = self.next_id("notifications")
            self.add("notifications", notice)


class FarmService:
    def __init__(self, repository: FarmRepository) -> None:
        self._repo = repository
        self._center = NotificationCenter()
        self._center.subscribe(LowMoistureObserver())

    @property
    def repo(self) -> FarmRepository:
        return self._repo

    def add_device(self, dtype: str, device_id: str, name: str, location: str, parameter: str) -> Device:
        device = DeviceFactory.create_device(dtype, device_id, name, location, parameter)
        if any(item.device_id == device.device_id for item in self._repo.all("devices")):
            raise ValidationError("รหัสอุปกรณ์ซ้ำกัน")
        return self._repo.add("devices", device)

    def record_sensor(self, device_id: str, moisture: float, temp: float) -> List[Notification]:
        if not any(device.device_id == device_id for device in self._repo.all("devices")):
            raise ValidationError("ไม่พบอุปกรณ์เซนเซอร์")
        data = self._repo.add("sensor_data", SensorData(self._repo.next_id("sensor_data"), device_id, moisture, temp))
        notices = self._center.notify(data)
        for notice in notices:
            notice._notification_id = self._repo.next_id("notifications")
            self._repo.add("notifications", notice)
        return notices

    def calculate_irrigation(self, plot_name: str, strategy: IIrrigationStrategy, current: float, target: float) -> IrrigationTask:
        water = strategy.calculate_water(current, target)
        if water <= 0:
            raise ValidationError("ความชื้นถึงเป้าหมายแล้ว ยังไม่ต้องรดน้ำ")
        task = IrrigationTask(self._repo.next_id("irrigation_tasks"), plot_name, water)
        return self._repo.add("irrigation_tasks", task)

    def add_harvest(self, crop_name: str, yield_kg: float, revenue: float) -> HarvestRecord:
        record = HarvestRecord(self._repo.next_id("harvest_records"), crop_name, yield_kg, revenue)
        return self._repo.add("harvest_records", record)


# ============================= UI helpers =============================
def get_state() -> tuple[FarmRepository, FarmService, UserRepository]:
    if "farm_repository" not in st.session_state:
        st.session_state.farm_repository = FarmRepository()
        st.session_state.farm_service = FarmService(st.session_state.farm_repository)
    if "user_repository" not in st.session_state:
        st.session_state.user_repository = UserRepository()
        for user in st.session_state.farm_repository.all("users"):
            st.session_state.user_repository.add_existing(user)
    if "current_user_id" not in st.session_state:
        st.session_state.current_user_id = 3
    return st.session_state.farm_repository, st.session_state.farm_service, st.session_state.user_repository


def frame(table: str, rows: Iterable[Dict[str, Any]]) -> None:
    st.dataframe(pd.DataFrame(list(rows)), use_container_width=True, hide_index=True)


def run_tests() -> tuple[str, unittest.TestResult]:
    repo = FarmRepository(seed=False)

    class SmartFarmTests(unittest.TestCase):
        def test_user_permissions_and_crud(self) -> None:
            users = UserRepository()
            farmer = users.add("ชาวสวน", "farmer@test.com", "1234", "เกษตรกร")
            self.assertIsInstance(farmer, Farmer)
            self.assertIn("บันทึกผลผลิต", farmer.get_permissions())
            users.update(farmer.user_id, "ชาวสวนใหม่", "farmer2@test.com", "ผู้ดูแลระบบ")
            self.assertIsInstance(users.get(farmer.user_id), Admin)
            users.deactivate(farmer.user_id)
            self.assertFalse(users.get(farmer.user_id).is_active)
            users.delete(farmer.user_id)
            self.assertIsNone(users.get(farmer.user_id))

        def test_super_admin_permissions(self) -> None:
            super_admin = SuperAdmin(1, "root", "root@test.com", "1234")
            self.assertIn("สิทธิ์ทั้งหมด", super_admin.get_permissions())

        def test_factory_polymorphism(self) -> None:
            sensor = DeviceFactory.create_device("sensor", "S-1", "ทดสอบ", "A1", "ความชื้น")
            actuator = DeviceFactory.create_device("actuator", "V-1", "ทดสอบ", "A1", "10")
            self.assertIsInstance(sensor, SensorDevice)
            self.assertIsInstance(actuator, ActuatorDevice)
            self.assertNotEqual(sensor.execute_action(), actuator.execute_action())

        def test_strategy(self) -> None:
            self.assertEqual(MoistureBasedStrategy().calculate_water(30, 60), 75)
            self.assertEqual(TimerBasedStrategy().calculate_water(30, 60), 15)

        def test_validation(self) -> None:
            with self.assertRaises(ValidationError):
                Plot(1, "แปลงผิด", -1)
            with self.assertRaises(ValidationError):
                HarvestRecord(1, "ผัก", 0, 100)

        def test_observer(self) -> None:
            center = NotificationCenter()
            center.subscribe(LowMoistureObserver())
            self.assertEqual(len(center.notify(SensorData(1, "S-1", 20, 25))), 1)

        def test_integration_service(self) -> None:
            service = FarmService(repo)
            device = service.add_device("sensor", "S-99", "เซนเซอร์", "A1", "ความชื้น")
            self.assertEqual(device.device_id, "S-99")
            self.assertEqual(len(service.record_sensor("S-99", 20, 25)), 1)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SmartFarmTests)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    return output.getvalue(), result


# ============================= Streamlit presentation =============================
st.set_page_config(page_title="Smart Farm Management System", page_icon="🌱", layout="wide")
st.markdown("""<style>
.main { background: #f4f8f0; }
[data-testid="stMetric"] { background: white; border: 1px solid #d9e6d0; padding: 12px; border-radius: 10px; }
</style>""", unsafe_allow_html=True)

repo, service, user_repo = get_state()
farm = repo.all("farms")[0]
users = user_repo.all()
user_labels = {user.user_id: f"{user.username} ({user.role})" for user in users}
selected_id = st.sidebar.selectbox("ผู้ใช้จำลอง (Authentication)", list(user_labels), format_func=lambda value: user_labels[value], index=0)
st.session_state.current_user_id = selected_id
current_user = user_repo.get(selected_id)
st.sidebar.markdown(f"**ผู้ใช้งาน:** {current_user.username if current_user else '-'}")
st.sidebar.markdown(f"**บทบาท:** `{current_user.role if current_user else '-'}`")
st.sidebar.markdown("**สิทธิ์:** " + ", ".join(current_user.get_permissions()) if current_user else "")
all_menus = ["📊 Dashboard", "🧩 สถาปัตยกรรมและ Checklist", "👥 จัดการผู้ใช้งาน", "📡 อุปกรณ์ฮาร์ดแวร์", "💧 คำนวณการรดน้ำ", "🌾 ผลผลิตและรายได้", "🌐 REST API Simulator", "🧪 Unit & Integration Testing"]
restricted = {"👥 จัดการผู้ใช้งาน", "🌐 REST API Simulator", "🧪 Unit & Integration Testing"}
allowed_menus = [item for item in all_menus if item not in restricted or (current_user and current_user.role in {"ผู้ดูแลระบบ", "ซูเปอร์แอดมิน"})]
menu = st.sidebar.radio("เมนูหลัก", allowed_menus)
st.title("🌱 ระบบจัดการฟาร์มอัจฉริยะ")
st.caption("Smart Farm Management System | Full Stack OOP Project Standard")

if menu == "📊 Dashboard":
    st.header("📊 ภาพรวมฟาร์ม")
    harvests = repo.all("harvest_records")
    cards = st.columns(4)
    cards[0].metric("ฟาร์ม", len(repo.all("farms")))
    cards[1].metric("แปลงปลูก", len(repo.all("plots")))
    cards[2].metric("พืชกำลังปลูก", sum(c.status == "กำลังปลูก" for c in repo.all("crops")))
    cards[3].metric("ผลผลิตสะสม", f"{sum(h.yield_kg for h in harvests):,.1f} กก.")
    left, right = st.columns(2)
    with left:
        frame("sensor_data", [{"อุปกรณ์": s.device_id, "ความชื้น": f"{s.moisture}%", "อุณหภูมิ": f"{s.temp} °C", "เวลา": s.timestamp} for s in repo.all("sensor_data")])
    with right:
        st.subheader("🔔 การแจ้งเตือน")
        for notice in repo.all("notifications"):
            st.warning(f"[{notice.created_at}] {notice.message}")

elif menu == "🧩 สถาปัตยกรรมและ Checklist":
    st.header("🧩 สถาปัตยกรรม OOP และ Full Stack Checklist")
    st.markdown("""**Domain Classes (13 คลาส):** `User`, `Farmer`, `Admin`, `Device`, `SensorDevice`, `ActuatorDevice`, `Farm`, `Plot`, `Crop`, `SensorData`, `IrrigationTask`, `HarvestRecord`, `Notification`  
**Patterns:** `DeviceFactory`, `MoistureBasedStrategy`, `TimerBasedStrategy`, `FarmRepository`, `NotificationCenter`  
**ความสัมพันธ์:** Farm composition กับ Plot, Plot aggregation กับ Crop, Farmer association กับ Farm, inheritance ของ User และ Device""")
    st.subheader("ตารางข้อมูลจำลอง 10 ตาราง")
    frame("tables", [{"ตาราง": table, "รายการ": len(repo.all(table))} for table in FarmRepository.TABLES])
    st.subheader("Business Rules (12 ข้อ)")
    st.markdown("""1. ข้อมูลสำคัญต้องไม่ว่าง  
2. อีเมลต้องมีรูปแบบถูกต้อง  
3. รหัสอุปกรณ์ต้องไม่ซ้ำ  
4. พื้นที่แปลงต้องมากกว่า 0  
5. พืชในแปลงเดียวกันปลูกพร้อมกันได้หนึ่งรายการ  
6. ความชื้นอยู่ระหว่าง 0-100%  
7. อุณหภูมิอยู่ในช่วงที่รองรับ  
8. ความชื้นต่ำกว่า 30% สร้าง Notification  
9. ปริมาณน้ำต้องมากกว่า 0  
10. ผลผลิตต้องมากกว่า 0  
11. รายได้ต้องไม่ติดลบ  
12. Actuator ต้องมีอัตราการไหลมากกว่า 0""")
    st.subheader("Use Cases (12 รายการ)")
    st.write("เข้าสู่ระบบ, สลับบทบาท, ดู Dashboard, จัดการฟาร์ม, จัดการแปลง, จัดการพืช, สร้างอุปกรณ์, รับ telemetry, คำนวณน้ำ, สร้างงานรดน้ำ, บันทึกผลผลิต, ตรวจสอบแจ้งเตือน")

elif menu == "👥 จัดการผู้ใช้งาน":
    st.header("👥 จัดการผู้ใช้งาน (User Management System)")
    if not current_user or current_user.role not in {"ผู้ดูแลระบบ", "ซูเปอร์แอดมิน"}:
        st.error("คุณไม่มีสิทธิ์เข้าถึงเมนูนี้")
    else:
        st.subheader("📋 รายชื่อผู้ใช้งานทั้งหมด")
        frame("users", [{
            "ID": user.user_id,
            "Username": user.username,
            "Email": user.email,
            "Role": user.role,
            "สิทธิ์การใช้งาน": ", ".join(user.get_permissions()),
            "สถานะ": "ใช้งานอยู่" if user.is_active else "ปิดใช้งาน",
        } for user in user_repo.all()])
        create_tab, update_tab, account_tab = st.tabs(["➕ สร้างผู้ใช้ใหม่", "✏️ แก้ไขผู้ใช้และสิทธิ์", "🗑️ จัดการสถานะบัญชี"])
        with create_tab:
            with st.form("create_user_form"):
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
                new_password = st.text_input("รหัสผ่าน", type="password")
                new_role = st.selectbox("ระดับสิทธิ์", list(UserRepository.ROLE_TYPES))
                create_submitted = st.form_submit_button("สร้างผู้ใช้งาน")
            if create_submitted:
                try:
                    user_repo.add(new_username, new_email, new_password, new_role)
                    st.success("สร้างผู้ใช้งานสำเร็จ")
                    st.rerun()
                except (ValidationError, ValueError) as error:
                    st.error(f"ไม่สามารถสร้างผู้ใช้: {error}")
        with update_tab:
            editable_users = user_repo.all()
            edit_id = st.selectbox("เลือกผู้ใช้", [user.user_id for user in editable_users], format_func=lambda value: user_labels.get(value, f"ผู้ใช้ {value}"))
            edit_user = user_repo.get(edit_id)
            with st.form("update_user_form"):
                edit_username = st.text_input("Username ใหม่", value=edit_user.username if edit_user else "")
                edit_email = st.text_input("Email ใหม่", value=edit_user.email if edit_user else "")
                edit_role = st.selectbox("บทบาทใหม่", list(UserRepository.ROLE_TYPES), index=list(UserRepository.ROLE_TYPES).index(edit_user.role) if edit_user and edit_user.role in UserRepository.ROLE_TYPES else 0)
                update_submitted = st.form_submit_button("บันทึกการแก้ไข")
            if update_submitted:
                try:
                    user_repo.update(edit_id, edit_username, edit_email, edit_role)
                    st.success("อัปเดตข้อมูลและสิทธิ์สำเร็จ")
                    st.rerun()
                except (ValidationError, ValueError) as error:
                    st.error(f"ไม่สามารถอัปเดตผู้ใช้: {error}")
        with account_tab:
            action_id = st.selectbox("เลือกบัญชี", [user.user_id for user in user_repo.all()], format_func=lambda value: user_labels.get(value, f"ผู้ใช้ {value}"))
            action = st.radio("การทำงาน", ["ปิดการใช้งาน", "เปิดใช้งาน", "ลบถาวร"], horizontal=True)
            if st.button("ยืนยันการเปลี่ยนแปลงบัญชี"):
                try:
                    if action == "ปิดการใช้งาน":
                        user_repo.deactivate(action_id)
                    elif action == "เปิดใช้งาน":
                        user_repo.activate(action_id)
                    else:
                        if action_id == current_user.user_id:
                            raise ValidationError("ไม่สามารถลบบัญชีที่กำลังใช้งานอยู่")
                        user_repo.delete(action_id)
                    st.success("ดำเนินการกับบัญชีสำเร็จ")
                    st.rerun()
                except (ValidationError, ValueError) as error:
                    st.error(f"ไม่สามารถดำเนินการ: {error}")

elif menu == "📡 อุปกรณ์ฮาร์ดแวร์":
    st.header("📡 จัดการอุปกรณ์ด้วย Factory Pattern")
    with st.form("device_form"):
        dtype = st.selectbox("ชนิดอุปกรณ์", ["Sensor", "Actuator"])
        device_id = st.text_input("รหัสอุปกรณ์", "DEV-003")
        name = st.text_input("ชื่ออุปกรณ์", "อุปกรณ์โซน B")
        location = st.text_input("ตำแหน่ง", "แปลง B1")
        parameter = st.text_input("ประเภทเซนเซอร์ / อัตราการไหล", "ความชื้นในดิน" if dtype == "Sensor" else "30.5")
        submitted = st.form_submit_button("สร้างอุปกรณ์")
    if submitted:
        try:
            device = service.add_device(dtype, device_id, name, location, parameter)
            st.success(device.execute_action())
        except (ValidationError, ValueError) as error:
            st.error(f"Validation Error: {error}")
    rows = []
    for device in repo.all("devices"):
        if isinstance(device, SensorDevice):
            device_type, state, action = device.sensor_type, "ออนไลน์" if device.is_active else "ออฟไลน์", device.execute_action()
        elif isinstance(device, ActuatorDevice):
            device_type, state, action = "วาล์วน้ำ", device.state, device.execute_action()
        else:
            device_type, state, action = "อุปกรณ์ทั่วไป", "ออนไลน์" if device.is_active else "ออฟไลน์", device.execute_action()
        rows.append({"รหัส": device.device_id, "ชื่อ": device.name, "ประเภท": device_type, "ตำแหน่ง": device.location, "สถานะ": state, "การทำงาน": action})
    frame("devices", rows)

elif menu == "💧 คำนวณการรดน้ำ":
    st.header("💧 คำนวณการรดน้ำด้วย Strategy Pattern")
    plot_names = [plot.name for plot in farm.plots]
    plot_name = st.selectbox("เลือกแปลง", plot_names)
    current = st.number_input("ความชื้นปัจจุบัน (%)", 0.0, 100.0, 25.0)
    target = st.number_input("ความชื้นเป้าหมาย (%)", 0.0, 100.0, 65.0)
    strategy_name = st.radio("กลยุทธ์", ["ตามความชื้น", "ตามเวลาคงที่"])
    if st.button("คำนวณและสร้างงาน"):
        try:
            strategy = MoistureBasedStrategy() if strategy_name == "ตามความชื้น" else TimerBasedStrategy()
            task = service.calculate_irrigation(plot_name, strategy, current, target)
            st.success(f"ต้องใช้น้ำ {task.water_amount:,.2f} ลิตร")
        except ValidationError as error:
            st.warning(str(error))
    frame("irrigation_tasks", [{"แปลง": t.plot_name, "น้ำ (ลิตร)": t.water_amount, "สถานะ": t.status} for t in repo.all("irrigation_tasks")])

elif menu == "🌾 ผลผลิตและรายได้":
    st.header("🌾 รายงานผลผลิตและรายได้")
    with st.form("harvest_form"):
        crop_name = st.text_input("ชื่อพืช", "ผักสลัด Green Oak")
        yield_kg = st.number_input("ผลผลิต (กก.)", min_value=0.0, value=50.0)
        revenue = st.number_input("รายได้ (บาท)", min_value=0.0, value=4000.0)
        submitted = st.form_submit_button("บันทึกผลผลิต")
    if submitted:
        try:
            service.add_harvest(crop_name, yield_kg, revenue)
            st.success("บันทึกผลผลิตสำเร็จ")
        except ValidationError as error:
            st.error(str(error))
    frame("harvest_records", [{"รหัส": h.record_id, "พืช": h.crop_name, "ผลผลิต (กก.)": h.yield_kg, "รายได้ (บาท)": h.revenue, "วันที่": h.harvest_date} for h in repo.all("harvest_records")])
    st.metric("รายได้รวม", f"{sum(h.revenue for h in repo.all('harvest_records')):,.2f} บาท")

elif menu == "🌐 REST API Simulator":
    st.header("🌐 REST API Endpoints Simulator")
    endpoints = [("POST", "/api/v1/auth/login", "เข้าสู่ระบบ"), ("POST", "/api/v1/auth/register", "สมัครสมาชิก"), ("GET", "/api/v1/users/me", "โปรไฟล์"), ("GET", "/api/v1/roles", "บทบาท"), ("GET", "/api/v1/farms", "รายการฟาร์ม"), ("POST", "/api/v1/farms", "สร้างฟาร์ม"), ("GET", "/api/v1/farms/{id}", "ฟาร์มตามรหัส"), ("PUT", "/api/v1/farms/{id}", "แก้ไขฟาร์ม"), ("DELETE", "/api/v1/farms/{id}", "ลบฟาร์ม"), ("GET", "/api/v1/plots", "รายการแปลง"), ("POST", "/api/v1/plots", "สร้างแปลง"), ("PUT", "/api/v1/plots/{id}", "แก้ไขแปลง"), ("GET", "/api/v1/crops", "รายการพืช"), ("POST", "/api/v1/crops", "สร้างพืช"), ("GET", "/api/v1/devices", "รายการอุปกรณ์"), ("POST", "/api/v1/devices", "ลงทะเบียนอุปกรณ์"), ("POST", "/api/v1/sensors/telemetry", "รับค่าเซนเซอร์"), ("GET", "/api/v1/sensors/{id}/history", "ประวัติเซนเซอร์"), ("POST", "/api/v1/irrigation/trigger", "สั่งรดน้ำ"), ("GET", "/api/v1/irrigation/logs", "ประวัติรดน้ำ"), ("POST", "/api/v1/harvests", "บันทึกผลผลิต"), ("GET", "/api/v1/harvests/reports", "รายงานผลผลิต")]
    frame("api", [{"Method": method, "Endpoint": path, "คำอธิบาย": description} for method, path, description in endpoints])
    st.success(f"จำลองทั้งหมด {len(endpoints)} endpoints")

else:
    st.header("🧪 Unit & Integration Testing Suite")
    st.write("ทดสอบ Domain Classes, Design Patterns, Validation และการทำงานร่วมกันของ Service")
    if st.button("🚀 รันการทดสอบทั้งหมด"):
        output, result = run_tests()
        st.code(output)
        if result.wasSuccessful():
            st.success(f"ผ่านทั้งหมด {result.testsRun} tests")
        else:
            st.error(f"ไม่ผ่าน {len(result.failures) + len(result.errors)} tests")
