"""ระบบจัดการฟาร์มอัจฉริยะ: Full Stack OOP Demonstration."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional
import hashlib

import pandas as pd
import plotly.express as px
import streamlit as st


class ValidationError(ValueError):
    """ข้อผิดพลาดจากข้อมูลนำเข้าที่ไม่ผ่านกฎธุรกิจ"""


class User:
    def __init__(self, user_id: int, name: str, email: str, password: str) -> None:
        self._user_id = self._positive_int(user_id, "รหัสผู้ใช้")
        self._name = self._required(name, "ชื่อผู้ใช้")
        self._email = self._required(email, "อีเมล").lower()
        self._password_hash = self._hash_password(password)

    @staticmethod
    def _required(value: str, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label}ต้องไม่ว่าง")
        return value.strip()

    @staticmethod
    def _positive_int(value: int, label: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(f"{label}ต้องเป็นจำนวนเต็มบวก")
        return value

    @staticmethod
    def _hash_password(password: str) -> str:
        if not isinstance(password, str) or len(password) < 4:
            raise ValidationError("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    def authenticate(self, password: str) -> bool:
        return self._password_hash == self._hash_password(password)


class Farmer(User):
    def __init__(self, user_id: int, name: str, email: str, password: str) -> None:
        super().__init__(user_id, name, email, password)
        self._farms: List[Farm] = []

    @property
    def farms(self) -> List[Farm]:
        return list(self._farms)

    def assign_farm(self, farm: Farm) -> None:
        if farm not in self._farms:
            self._farms.append(farm)


class Admin(User):
    @property
    def role(self) -> str:
        return "ผู้ดูแลระบบ"


class Device(ABC):
    def __init__(self, device_id: int, name: str, plot_id: int) -> None:
        self._device_id = self._positive(device_id, "รหัสอุปกรณ์")
        self._name = self._required(name, "ชื่ออุปกรณ์")
        self._plot_id = self._positive(plot_id, "รหัสแปลง")
        self._is_online = True

    @staticmethod
    def _required(value: str, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label}ต้องไม่ว่าง")
        return value.strip()

    @staticmethod
    def _positive(value: int, label: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(f"{label}ต้องเป็นจำนวนเต็มบวก")
        return value

    @property
    def device_id(self) -> int:
        return self._device_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def plot_id(self) -> int:
        return self._plot_id

    @property
    def is_online(self) -> bool:
        return self._is_online

    def set_online(self, online: bool) -> None:
        self._is_online = bool(online)

    @abstractmethod
    def execute_action(self, action: str) -> str:
        raise NotImplementedError


class SensorDevice(Device):
    def __init__(self, device_id: int, name: str, plot_id: int, sensor_type: str) -> None:
        super().__init__(device_id, name, plot_id)
        self._sensor_type = self._required(sensor_type, "ประเภทเซนเซอร์")

    @property
    def sensor_type(self) -> str:
        return self._sensor_type

    def execute_action(self, action: str) -> str:
        return f"อ่านค่า{self._sensor_type}จาก {self._name} สำเร็จ ({action})"


class ActuatorDevice(Device):
    def __init__(self, device_id: int, name: str, plot_id: int, actuator_type: str) -> None:
        super().__init__(device_id, name, plot_id)
        self._actuator_type = self._required(actuator_type, "ประเภทแอคชูเอเตอร์")
        self._state = "ปิด"

    @property
    def actuator_type(self) -> str:
        return self._actuator_type

    @property
    def state(self) -> str:
        return self._state

    def execute_action(self, action: str) -> str:
        if action not in {"เปิด", "ปิด"}:
            raise ValidationError("คำสั่งอุปกรณ์ต้องเป็น เปิด หรือ ปิด")
        self._state = action
        return f"{self._name} เปลี่ยนสถานะเป็น {action}แล้ว"


class Crop:
    def __init__(self, crop_id: int, name: str, plant_date: date, status: str = "กำลังปลูก") -> None:
        if not name or not name.strip():
            raise ValidationError("ชื่อพืชต้องไม่ว่าง")
        self._crop_id, self._name = crop_id, name.strip()
        self._plant_date, self._status = plant_date, status

    @property
    def crop_id(self) -> int:
        return self._crop_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def plant_date(self) -> date:
        return self._plant_date

    @property
    def status(self) -> str:
        return self._status

    def mark_harvested(self) -> None:
        self._status = "เก็บเกี่ยวแล้ว"


class Plot:
    def __init__(self, plot_id: int, name: str, area_sqm: float) -> None:
        if area_sqm <= 0:
            raise ValidationError("พื้นที่แปลงต้องมากกว่า 0")
        if not name or not name.strip():
            raise ValidationError("ชื่อแปลงต้องไม่ว่าง")
        self._plot_id, self._name = plot_id, name.strip()
        self._area_sqm = float(area_sqm)
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

    def add_crop(self, crop: Crop) -> None:
        if any(item.status == "กำลังปลูก" for item in self._crops):
            raise ValidationError("หนึ่งแปลงมีพืชที่กำลังปลูกได้ครั้งละหนึ่งรายการ")
        self._crops.append(crop)


class Farm:
    def __init__(self, farm_id: int, name: str, location: str, farmer_id: int) -> None:
        if not name.strip() or not location.strip():
            raise ValidationError("ชื่อฟาร์มและสถานที่ตั้งต้องไม่ว่าง")
        self._farm_id, self._name = farm_id, name.strip()
        self._location, self._farmer_id = location.strip(), farmer_id
        self._plots: List[Plot] = []

    @property
    def farm_id(self) -> int:
        return self._farm_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def location(self) -> str:
        return self._location

    @property
    def farmer_id(self) -> int:
        return self._farmer_id

    @property
    def plots(self) -> List[Plot]:
        return list(self._plots)

    def add_plot(self, plot: Plot) -> None:
        if any(item.name.lower() == plot.name.lower() for item in self._plots):
            raise ValidationError("ชื่อแปลงในฟาร์มนี้ซ้ำกัน")
        self._plots.append(plot)


class SensorData:
    def __init__(self, record_id: int, plot_id: int, sensor_type: str, value: float, recorded_at: Optional[datetime] = None) -> None:
        if not sensor_type.strip() or not isinstance(value, (int, float)):
            raise ValidationError("ประเภทและค่าของเซนเซอร์ไม่ถูกต้อง")
        if sensor_type == "ความชื้นในดิน" and not 0 <= value <= 100:
            raise ValidationError("ความชื้นในดินต้องอยู่ระหว่าง 0-100%")
        self._record_id, self._plot_id = record_id, plot_id
        self._sensor_type, self._value = sensor_type, float(value)
        self._recorded_at = recorded_at or datetime.now()

    @property
    def record_id(self) -> int:
        return self._record_id

    @property
    def plot_id(self) -> int:
        return self._plot_id

    @property
    def sensor_type(self) -> str:
        return self._sensor_type

    @property
    def value(self) -> float:
        return self._value

    @property
    def recorded_at(self) -> datetime:
        return self._recorded_at


class IrrigationTask:
    def __init__(self, task_id: int, plot_id: int, duration_minutes: int, mode: str, status: str = "รอดำเนินการ") -> None:
        if duration_minutes <= 0 or duration_minutes > 240:
            raise ValidationError("ระยะเวลารดน้ำต้องอยู่ระหว่าง 1-240 นาที")
        self._task_id, self._plot_id = task_id, plot_id
        self._duration_minutes, self._mode, self._status = duration_minutes, mode, status
        self._created_at = datetime.now()

    @property
    def task_id(self) -> int:
        return self._task_id

    @property
    def plot_id(self) -> int:
        return self._plot_id

    @property
    def duration_minutes(self) -> int:
        return self._duration_minutes

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def status(self) -> str:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    def complete(self) -> None:
        self._status = "เสร็จสิ้น"


class HarvestRecord:
    def __init__(self, record_id: int, crop_id: int, crop_name: str, harvest_date: date, yield_kg: float, revenue: float) -> None:
        if yield_kg <= 0 or revenue < 0:
            raise ValidationError("ผลผลิตต้องมากกว่า 0 และรายได้ต้องไม่ติดลบ")
        self._record_id, self._crop_id, self._crop_name = record_id, crop_id, crop_name
        self._harvest_date, self._yield_kg, self._revenue = harvest_date, float(yield_kg), float(revenue)

    @property
    def record_id(self) -> int:
        return self._record_id

    @property
    def crop_id(self) -> int:
        return self._crop_id

    @property
    def crop_name(self) -> str:
        return self._crop_name

    @property
    def harvest_date(self) -> date:
        return self._harvest_date

    @property
    def yield_kg(self) -> float:
        return self._yield_kg

    @property
    def revenue(self) -> float:
        return self._revenue


class Notification:
    def __init__(self, notification_id: int, title: str, message: str, severity: str = "แจ้งเตือน") -> None:
        self._notification_id, self._title, self._message = notification_id, title, message
        self._severity, self._created_at, self._is_read = severity, datetime.now(), False

    @property
    def notification_id(self) -> int:
        return self._notification_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def message(self) -> str:
        return self._message

    @property
    def severity(self) -> str:
        return self._severity

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def is_read(self) -> bool:
        return self._is_read

    def mark_read(self) -> None:
        self._is_read = True


class DeviceFactory:
    @staticmethod
    def create(device_type: str, device_id: int, name: str, plot_id: int) -> Device:
        if device_type == "เซนเซอร์ความชื้น":
            return SensorDevice(device_id, name, plot_id, "ความชื้นในดิน")
        if device_type == "เซนเซอร์อุณหภูมิ":
            return SensorDevice(device_id, name, plot_id, "อุณหภูมิ")
        if device_type == "วาล์วรดน้ำ":
            return ActuatorDevice(device_id, name, plot_id, "วาล์วน้ำ")
        raise ValidationError("ไม่รู้จักประเภทอุปกรณ์")


class IIrrigationStrategy(ABC):
    @abstractmethod
    def calculate_duration(self, moisture: float, area_sqm: float) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class MoistureBasedStrategy(IIrrigationStrategy):
    @property
    def name(self) -> str:
        return "ตามความชื้น"

    def calculate_duration(self, moisture: float, area_sqm: float) -> int:
        if not 0 <= moisture <= 100 or area_sqm <= 0:
            raise ValidationError("ค่าความชื้นหรือพื้นที่ไม่ถูกต้อง")
        return max(5, min(120, round((55 - moisture) * area_sqm / 12))) if moisture < 55 else 0


class TimerBasedStrategy(IIrrigationStrategy):
    @property
    def name(self) -> str:
        return "ตามเวลา"

    def calculate_duration(self, moisture: float, area_sqm: float) -> int:
        if area_sqm <= 0:
            raise ValidationError("พื้นที่ต้องมากกว่า 0")
        return max(5, min(120, round(area_sqm / 2)))


class NotificationObserver:
    def update(self, data: SensorData) -> Optional[Notification]:
        if data.sensor_type == "ความชื้นในดิน" and data.value < 30:
            return Notification(0, "ความชื้นต่ำ", f"แปลง {data.plot_id} มีความชื้นเพียง {data.value:.1f}%", "เร่งด่วน")
        return None


class NotificationCenter:
    def __init__(self) -> None:
        self._observers: List[NotificationObserver] = []

    def subscribe(self, observer: NotificationObserver) -> None:
        self._observers.append(observer)

    def publish(self, data: SensorData) -> List[Notification]:
        notices: List[Notification] = []
        for observer in self._observers:
            notice = observer.update(data)
            if notice:
                notices.append(notice)
        return notices


class FarmRepository:
    """Repository จำลอง persistence โดยรักษาข้อมูลใน session ของ Streamlit."""
    TABLES = ["users", "farms", "plots", "crops", "devices", "sensor_data", "irrigation_tasks", "harvest_records", "notifications", "audit_logs"]

    def __init__(self) -> None:
        self._data: Dict[str, List[Any]] = {table: [] for table in self.TABLES}
        self._sequences = {table: 0 for table in self.TABLES}

    def next_id(self, table: str) -> int:
        self._sequences[table] += 1
        return self._sequences[table]

    def add(self, table: str, item: Any) -> Any:
        self._data[table].append(item)
        return item

    def all(self, table: str) -> List[Any]:
        return list(self._data[table])

    def get(self, table: str, item_id: int, attr: str) -> Optional[Any]:
        return next((item for item in self._data[table] if getattr(item, attr, None) == item_id), None)


class SmartFarmService:
    def __init__(self, repository: FarmRepository) -> None:
        self.repo = repository
        self.notifications = NotificationCenter()
        self.notifications.subscribe(NotificationObserver())

    def add_farm(self, name: str, location: str, farmer: Farmer) -> Farm:
        farm = Farm(self.repo.next_id("farms"), name, location, farmer.user_id)
        self.repo.add("farms", farm)
        farmer.assign_farm(farm)
        return farm

    def add_plot(self, farm_id: int, name: str, area: float) -> Plot:
        farm = self.repo.get("farms", farm_id, "farm_id")
        if not farm:
            raise ValidationError("ไม่พบฟาร์มที่เลือก")
        plot = Plot(self.repo.next_id("plots"), name, area)
        farm.add_plot(plot)
        return self.repo.add("plots", plot)

    def add_crop(self, plot_id: int, name: str, plant_date: date) -> Crop:
        plot = self.repo.get("plots", plot_id, "plot_id")
        if not plot:
            raise ValidationError("ไม่พบแปลงที่เลือก")
        crop = Crop(self.repo.next_id("crops"), name, plant_date)
        plot.add_crop(crop)
        return self.repo.add("crops", crop)

    def record_sensor(self, plot_id: int, sensor_type: str, value: float) -> List[Notification]:
        if not self.repo.get("plots", plot_id, "plot_id"):
            raise ValidationError("ไม่พบแปลงที่เลือก")
        record = SensorData(self.repo.next_id("sensor_data"), plot_id, sensor_type, value)
        self.repo.add("sensor_data", record)
        notices = self.notifications.publish(record)
        for notice in notices:
            notice._notification_id = self.repo.next_id("notifications")
            self.repo.add("notifications", notice)
        return notices

    def create_irrigation_task(self, plot_id: int, strategy: IIrrigationStrategy, moisture: float) -> IrrigationTask:
        plot = self.repo.get("plots", plot_id, "plot_id")
        if not plot:
            raise ValidationError("ไม่พบแปลงที่เลือก")
        duration = strategy.calculate_duration(moisture, plot.area_sqm)
        if duration == 0:
            raise ValidationError("ความชื้นเพียงพอ ยังไม่จำเป็นต้องรดน้ำ")
        task = IrrigationTask(self.repo.next_id("irrigation_tasks"), plot_id, duration, strategy.name)
        return self.repo.add("irrigation_tasks", task)

    def add_harvest(self, crop_id: int, harvest_date: date, yield_kg: float, revenue: float) -> HarvestRecord:
        crop = self.repo.get("crops", crop_id, "crop_id")
        if not crop or crop.status != "กำลังปลูก":
            raise ValidationError("เลือกได้เฉพาะพืชที่กำลังปลูก")
        record = HarvestRecord(self.repo.next_id("harvest_records"), crop_id, crop.name, harvest_date, yield_kg, revenue)
        crop.mark_harvested()
        return self.repo.add("harvest_records", record)


def get_service() -> SmartFarmService:
    if "farm_service" not in st.session_state:
        repository = FarmRepository()
        farmer = Farmer(repository.next_id("users"), "เกษตรกรตัวอย่าง", "farmer@example.com", "farm1234")
        repository.add("users", farmer)
        service = SmartFarmService(repository)
        farm = service.add_farm("ฟาร์มบ้านสุขใจ", "เชียงใหม่", farmer)
        plot = service.add_plot(farm.farm_id, "แปลงผัก A1", 120)
        service.add_crop(plot.plot_id, "ผักสลัด", date.today())
        service.record_sensor(plot.plot_id, "ความชื้นในดิน", 24)
        service.record_sensor(plot.plot_id, "อุณหภูมิ", 28.5)
        repository.add("devices", DeviceFactory.create("เซนเซอร์ความชื้น", repository.next_id("devices"), "เซนเซอร์ A1", plot.plot_id))
        repository.add("devices", DeviceFactory.create("วาล์วรดน้ำ", repository.next_id("devices"), "วาล์ว A1", plot.plot_id))
        st.session_state.farm_service = service
    return st.session_state.farm_service


st.set_page_config(page_title="Smart Farm Management System", page_icon="🌱", layout="wide")
st.markdown("""
<style>
.main { background: #f5f8f1; }
[data-testid="stMetric"] { background: white; border: 1px solid #dbe7d3; padding: 14px; border-radius: 12px; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

service = get_service()
repo = service.repo
farmer = next((user for user in repo.all("users") if isinstance(user, Farmer)), None)
st.title("🌱 ระบบจัดการฟาร์มอัจฉริยะ")
st.caption("Smart Farm Management System | Full Stack OOP Project Standard")

menu = ["📊 Dashboard", "🏗️ สถาปัตยกรรม OOP", "📡 จัดการอุปกรณ์ฮาร์ดแวร์", "💧 คำนวณการรดน้ำ", "📈 รายงานผลผลิตและรายได้"]
choice = st.sidebar.radio("เมนูหลัก", menu)
st.sidebar.info(f"ผู้ใช้งาน: {farmer.name if farmer else 'ผู้ดูแลระบบ'}\nบทบาท: เกษตรกร")


def plot_label(plot_id: int) -> str:
    plot = repo.get("plots", plot_id, "plot_id")
    return f"{plot.name} ({plot.area_sqm:.0f} ตร.ม.)" if plot else "ไม่พบแปลง"


def show_error(action: Callable[[], Any]) -> None:
    try:
        result = action()
        if result is not None:
            st.success("ดำเนินการสำเร็จ")
    except (ValidationError, ValueError) as error:
        st.error(str(error))


if choice == menu[0]:
    st.header("📊 ภาพรวมฟาร์ม")
    harvests, notices = repo.all("harvest_records"), repo.all("notifications")
    metrics = st.columns(5)
    metrics[0].metric("ฟาร์ม", len(repo.all("farms")))
    metrics[1].metric("แปลงปลูก", len(repo.all("plots")))
    metrics[2].metric("พืชกำลังปลูก", sum(c.status == "กำลังปลูก" for c in repo.all("crops")))
    metrics[3].metric("ผลผลิตรวม", f"{sum(h.yield_kg for h in harvests):,.1f} กก.")
    metrics[4].metric("รายได้รวม", f"{sum(h.revenue for h in harvests):,.0f} บาท")
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("สถานะเซนเซอร์ล่าสุด")
        sensor_rows = [{"ประเภท": d.sensor_type, "ค่า": d.value, "เวลา": d.recorded_at.strftime("%d/%m/%Y %H:%M")} for d in repo.all("sensor_data")]
        st.dataframe(pd.DataFrame(sensor_rows), use_container_width=True, hide_index=True)
    with right:
        st.subheader("🔔 การแจ้งเตือน")
        if notices:
            for notice in reversed(notices[-5:]):
                st.warning(f"**{notice.title}**: {notice.message}")
        else:
            st.success("ไม่มีการแจ้งเตือนใหม่")

elif choice == menu[1]:
    st.header("🏗️ โครงสร้างสถาปัตยกรรม OOP")
    st.markdown("""
    **Domain Classes (13 คลาส):** `User`, `Farmer`, `Admin`, `Device`, `SensorDevice`, `ActuatorDevice`, `Farm`, `Plot`, `Crop`, `SensorData`, `IrrigationTask`, `HarvestRecord`, `Notification`

    **Patterns:** `DeviceFactory` สร้างอุปกรณ์ · `IIrrigationStrategy` รองรับอัลกอริทึมการรดน้ำ · `FarmRepository` จำลองตารางข้อมูล · `NotificationCenter` แจ้งเตือนผ่าน Observer

    **ความสัมพันธ์:** Farm composition กับ Plot, Plot aggregation กับ Crop, Farmer association กับ Farm และ inheritance ของ User/Device
    """)
    st.subheader("ตารางข้อมูลจำลอง")
    st.dataframe(pd.DataFrame({"ตาราง": FarmRepository.TABLES, "จำนวนรายการ": [len(repo.all(t)) for t in FarmRepository.TABLES]}), use_container_width=True, hide_index=True)
    st.subheader("Business Rules ที่บังคับใช้")
    rules = ["ชื่อข้อมูลสำคัญต้องไม่ว่าง", "รหัสต้องเป็นจำนวนเต็มบวก", "พื้นที่แปลงต้องมากกว่า 0", "พืชกำลังปลูกในแปลงเดียวกันมีได้หนึ่งรายการ", "ความชื้นอยู่ในช่วง 0-100%", "ความชื้นต่ำกว่า 30% สร้าง Notification", "ระยะเวลารดน้ำ 1-240 นาที", "ความชื้นพอไม่สร้างงานรดน้ำ", "เก็บเกี่ยวได้เฉพาะพืชที่กำลังปลูก", "ผลผลิตต้องมากกว่า 0", "รายได้ต้องไม่ติดลบ", "คำสั่ง actuator มีเพียงเปิด/ปิด"]
    st.dataframe(pd.DataFrame({"กฎธุรกิจ": rules}), use_container_width=True, hide_index=True)

elif choice == menu[2]:
    st.header("📡 จัดการอุปกรณ์ฮาร์ดแวร์")
    plots = repo.all("plots")
    with st.form("device_form"):
        device_type = st.selectbox("ประเภทอุปกรณ์ (Factory)", ["เซนเซอร์ความชื้น", "เซนเซอร์อุณหภูมิ", "วาล์วรดน้ำ"])
        name = st.text_input("ชื่ออุปกรณ์", placeholder="เช่น เซนเซอร์ B2")
        plot_id = st.selectbox("แปลงที่ติดตั้ง", [p.plot_id for p in plots], format_func=plot_label)
        submitted = st.form_submit_button("สร้างอุปกรณ์")
    if submitted:
        show_error(lambda: repo.add("devices", DeviceFactory.create(device_type, repo.next_id("devices"), name, plot_id)))
    rows = [{"รหัส": d.device_id, "ชื่อ": d.name, "ประเภท": getattr(d, "sensor_type", getattr(d, "actuator_type", "-")), "สถานะ": getattr(d, "state", "ออนไลน์"), "การทำงาน": d.execute_action("ตรวจสอบ") if isinstance(d, SensorDevice) else d.state} for d in repo.all("devices")]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif choice == menu[3]:
    st.header("💧 ระบบคำนวณการรดน้ำ")
    plots = repo.all("plots")
    with st.form("irrigation_form"):
        plot_id = st.selectbox("เลือกแปลง", [p.plot_id for p in plots], format_func=plot_label)
        strategy_name = st.radio("กลยุทธ์ (Strategy)", ["ตามความชื้น", "ตามเวลา"], horizontal=True)
        moisture = st.number_input("ความชื้นปัจจุบัน (%)", min_value=0.0, max_value=100.0, value=24.0)
        submitted = st.form_submit_button("คำนวณและสร้างงานรดน้ำ")
    if submitted:
        strategy = MoistureBasedStrategy() if strategy_name == "ตามความชื้น" else TimerBasedStrategy()
        show_error(lambda: service.create_irrigation_task(plot_id, strategy, moisture))
    tasks = [{"แปลง": plot_label(t.plot_id), "กลยุทธ์": t.mode, "ระยะเวลา (นาที)": t.duration_minutes, "สถานะ": t.status} for t in repo.all("irrigation_tasks")]
    st.dataframe(pd.DataFrame(tasks), use_container_width=True, hide_index=True)

else:
    st.header("📈 รายงานผลผลิตและรายได้")
    crops = repo.all("crops")
    with st.form("harvest_form"):
        available = [c for c in crops if c.status == "กำลังปลูก"]
        if available:
            crop_id = st.selectbox("พืชที่เก็บเกี่ยว", [c.crop_id for c in available], format_func=lambda cid: next(c.name for c in available if c.crop_id == cid))
            harvest_date = st.date_input("วันที่เก็บเกี่ยว", date.today())
            yield_kg = st.number_input("ผลผลิต (กิโลกรัม)", min_value=0.0, step=0.1)
            revenue = st.number_input("รายได้ (บาท)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("บันทึกผลผลิต")
            if submitted:
                show_error(lambda: service.add_harvest(crop_id, harvest_date, yield_kg, revenue))
        else:
            st.info("ไม่มีพืชที่พร้อมเก็บเกี่ยว")
    records = repo.all("harvest_records")
    if records:
        df = pd.DataFrame([{"วันที่": h.harvest_date, "พืช": h.crop_name, "ผลผลิต (กก.)": h.yield_kg, "รายได้ (บาท)": h.revenue} for h in records])
        st.dataframe(df, use_container_width=True, hide_index=True)
        chart_col, summary_col = st.columns(2)
        with chart_col:
            st.plotly_chart(px.bar(df, x="พืช", y="รายได้ (บาท)", color="พืช", title="รายได้แยกตามพืช"), use_container_width=True)
        with summary_col:
            st.plotly_chart(px.pie(df, names="พืช", values="ผลผลิต (กก.)", title="สัดส่วนผลผลิต"), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการเก็บเกี่ยว")
