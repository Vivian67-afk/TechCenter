CREATE DATABASE IF NOT EXISTS techcenter_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE techcenter_db;

CREATE TABLE usuarios (
  id_usuario INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  correo VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  rol ENUM('administrador','empleado') NOT NULL DEFAULT 'empleado',
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
  id_cliente INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  telefono VARCHAR(20),
  correo VARCHAR(120),
  direccion VARCHAR(200),
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicios (
  id_servicio INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  descripcion TEXT,
  precio DECIMAL(10,2) NOT NULL DEFAULT 0,
  duracion INT NOT NULL DEFAULT 30,
  estado TINYINT(1) NOT NULL DEFAULT 1,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reservaciones (
  id_reservacion INT AUTO_INCREMENT PRIMARY KEY,
  id_cliente INT NOT NULL,
  id_servicio INT NOT NULL,
  fecha DATE NOT NULL,
  hora TIME NOT NULL,
  estado ENUM('Pendiente','Confirmada','Atendida','Cancelada')
    NOT NULL DEFAULT 'Pendiente',
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_res_cliente FOREIGN KEY (id_cliente)
    REFERENCES clientes(id_cliente),
  CONSTRAINT fk_res_servicio FOREIGN KEY (id_servicio)
    REFERENCES servicios(id_servicio),
  INDEX idx_res_fecha_hora (fecha,hora)
);

CREATE TABLE bitacora (
  id_bitacora INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario INT NULL,
  accion VARCHAR(100) NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  descripcion TEXT,
  CONSTRAINT fk_bit_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario) ON DELETE SET NULL
);

INSERT INTO servicios (nombre,descripcion,precio,duracion,estado) VALUES
('Diagnóstico de equipo','Revisión general de computadora',250.00,60,1),
('Mantenimiento preventivo','Limpieza y revisión de componentes',450.00,90,1),
('Instalación de software','Instalación de software autorizado',180.00,45,1);