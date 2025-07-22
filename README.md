
# 📈 Finnhub Pipeline

Hệ thống thu thập, xử lý và hiển thị dữ liệu chứng khoán thời gian thực bằng cách kết hợp **Apache Spark**, **Apache Cassandra**, **Grafana**, và **Docker**.

---

## 📌 Mục tiêu dự án

Tự động hóa quy trình:
1. **Thu thập dữ liệu chứng khoán** từ API (Finnhub),
2. **Xử lý dữ liệu theo thời gian thực** với Apache Spark,
3. **Lưu trữ dữ liệu** trong Cassandra,
4. **Hiển thị dữ liệu trực quan** trên Grafana.

---

## 🧩 Kiến trúc hệ thống

```
       +-------------+       +--------------+       +-------------+       +-------------+
       |             |       |              |       |             |       |             |
       | finnhub API +-----> | finnhub-producer +-> | Spark Stream +---> |  Cassandra   |
       |             |       |              |       | Processor    |       |   DB        |
       +-------------+       +--------------+       +-------------+       +-------------+
                                                                        |
                                                                        v
                                                                    +-------+
                                                                    |Grafana|
                                                                    +-------+
```

---

## 📂 Cấu trúc thư mục

```
.
├── cassandra/                  # Cấu hình khởi tạo Cassandra (init.cql)
├── finnhub-producer/           # Thu thập dữ liệu từ API và đẩy vào Spark
│   ├── config.py               # Cấu hình API key & Kafka
│   ├── producer.py             # Script lấy dữ liệu từ Finnhub
│   ├── Dockerfile
│   └── requirements.txt
├── grafana/
│   ├── dashboards/             # Dashboard JSON cho Grafana
│   │   └── stock_dashboard.json
│   ├── provisioning/
│   │   ├── dashboards/         # Tự động tải dashboard
│   │   │   └── dashboard.yml
│   │   └── datasources/        # Cấu hình nguồn dữ liệu Cassandra
│   │       └── cassandra.yml
│   └── Dockerfile
├── spark-processor/            # Spark xử lý luồng dữ liệu
│   ├── stream_processor.py
│   ├── cassandra_config.py
│   ├── Dockerfile
│   └── requirements.txt
├── .env                        # Biến môi trường
├── .gitignore
└── docker-compose.yaml         # Chạy toàn bộ hệ thống
```

---

## 🚀 Cách chạy dự án

### 1. Chuẩn bị
- Docker & Docker Compose đã được cài đặt
- Tạo file `.env` chứa:
```env
FINNHUB_API_KEY=your_api_key_here
```

### 2. Chạy hệ thống
```bash
docker-compose up --build
```

### 3. Truy cập
- **Grafana UI**: [http://localhost:3000](http://localhost:3000)
  - Mặc định: `admin/admin`
- Dashboard: Tự động được tạo trong lần chạy đầu tiên.

---

## 🧪 Kiểm thử

- Kiểm tra log của từng service bằng:
```bash
docker-compose logs -f finnhub-producer
docker-compose logs -f spark-processor
docker-compose logs -f cassandra
docker-compose logs -f grafana
```

---

## 🔧 Mở rộng

- Hỗ trợ thêm nhiều loại tài sản tài chính (crypto, forex, etc.)
- Thêm khả năng cảnh báo từ Grafana
- Lưu lịch sử truy vấn để training mô hình AI dự báo