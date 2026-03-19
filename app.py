import streamlit as st
import requests
import time

st.set_page_config(
    page_title="Хостинг-Провайдер",
    layout="wide"
)

API_URL = "http://localhost:8000"

st.title("Облачный хостинг провайдер")

tab1, tab2 = st.tabs(["Список экземпляров", "Создать экземпляр"])

with tab1:
    st.header("Мои экземпляры")

    if st.button("Обновить список"):
        st.rerun()

    try:
        response = requests.get(f"{API_URL}/api/list")
        if response.status_code == 200:
            instances = response.json()["instances"]

            if not instances:
                st.info("У вас нет созданных экземпляров. Перейдите на вкладку 'Создать'!")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего экземпляров", len(instances))
                with col2:
                    running = sum(1 for i in instances if i["status"] == "running")
                    st.metric("Активные", running)
                with col3:
                    containers = sum(1 for i in instances if i["type"] == "container")
                    vms = sum(1 for i in instances if i["type"] == "vm")
                    st.metric("Контейнеры/ВМ", f"{containers}/{vms}")

                st.divider()

                for instance in instances:
                    with st.expander(f"{instance['name']} ({instance['id']})"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"Тип: {instance['type']}")
                            st.write(f"ОС: {instance['os']}")

                        with col2:
                            status = "🟢 Running" if instance['status'] == 'running' else '🔴 Stopped'
                            st.write(f"Статус: {status}")
                            st.write(f"Создан: {instance.get('created_at', 'N/A')[:19]}")

                        with col3:
                            st.write(f"CPU: {instance.get('cpu_limit', 'N/A')} ядер")
                            st.write(f"RAM: {instance.get('ram_limit', 'N/A')} MB")

                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if instance['status'] == 'running':
                                if st.button("Стоп", key=f"stop_{instance['id']}"):
                                    requests.post(f"{API_URL}/api/stop/{instance['id']}")
                                    st.success("Остановлен!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                if st.button("Старт", key=f"start_{instance['id']}"):
                                    requests.post(f"{API_URL}/api/start/{instance['id']}")
                                    st.success("Запущен!")
                                    time.sleep(1)
                                    st.rerun()

                        with col_b:
                            if st.button("Детали", key=f"details_{instance['id']}"):
                                st.json(instance)

                        with col_c:
                            if st.button("🗑 Удалить", key=f"delete_{instance['id']}"):
                                requests.delete(f"{API_URL}/api/delete/{instance['id']}")
                                st.success("Удален!")
                                time.sleep(1)
                                st.rerun()
        else:
            st.error("Ошибка загрузки данных")
    except Exception as e:
        st.error(f"Ошибка подключения к API: {e}")
        st.info("Убедитесь, что backend запущен на порту 8000")

with tab2:
    st.header("Создать новый экземпляр")

    with st.form("create_form"):
        col1, col2 = st.columns(2)
        with col1:
            instance_type = st.selectbox(
                "Тип экземпляра",
                ["container", "vm"],
                format_func=lambda x: "Контейнер (Docker)" if x == "container" else "Виртуальная машина (QEMU)"
            )

            os_options = {
                "container": ["ubuntu:latest", "alpine:latest", "centos:7", "debian:latest"],
                "vm": ["ubuntu-20.04", "centos-8", "debian-11", "alpine-3.16"]
            }

            selected_os = st.selectbox(
                "Операционная система",
                os_options[instance_type]
            )

        with col2:
            cpu = st.number_input("CPU (ядра)", min_value=1, max_value=8, value=2)
            ram = st.number_input("RAM (MB)", min_value=512, max_value=16384, value=2048, step=512)
            disk = st.number_input("Диск (GB)", min_value=10, max_value=100, value=20)

        name = st.text_input("Имя инстанса (опционально)", placeholder="my-server")

        submitted = st.form_submit_button("СОЗДАТЬ", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("Создание экземпляра"):
                config = {
                    "type": instance_type,
                    "os": selected_os,
                    "cpu": cpu,
                    "ram": ram,
                    "disk": disk,
                    "name": name if name else None
                }

                try:
                    response = requests.post(f"{API_URL}/api/create", json=config)
                    if response.status_code == 200:
                        st.success(f"Инстанс создан! ID: {response.json()['instance_id']}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Ошибка: {response.text}")
                except Exception as e:
                    st.error(f"Ошибка подключения к API: {e}")