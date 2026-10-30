import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. CONSTANTS, EARTH ROTATION & ATMOSPHERE
# ==========================================
G_EARTH = 9.80665          # Standard gravity (m/s^2)
R_EARTH = 6371000.0        # Earth radius (m)
RHO_0 = 1.225              # Sea level air density (kg/m^3)
H_SCALE = 8500.0           # Atmospheric scale height (m)

# Earth Rotation Parameters (e.g., Baikonur Cosmodrome Latitude ~ 46° N)
OMEGA_EARTH = 7.292115e-5  # Earth's angular velocity (rad/s)
LAUNCH_LATITUDE_DEG = 46.0 # Launch site latitude
# Initial horizontal velocity boost due to Earth's rotation (m/s)
V_EARTH_ROT = OMEGA_EARTH * R_EARTH * np.cos(np.radians(LAUNCH_LATITUDE_DEG))

def atmospheric_density(altitude):
    """Calculates air density decaying exponentially with altitude."""
    if altitude < 0:
        return RHO_0
    return RHO_0 * np.exp(-altitude / H_SCALE)

# ==========================================
# 2. ROCKET SPECIFICATIONS (Two-Stage)
# ==========================================
m_structure_s1 = 15000.0    # Dry mass (kg)
m_propellant_s1 = 120000.0  # Fuel mass (kg)
thrust_s1 = 2200000.0       # Thrust force (N)
burn_time_s1 = 80.0         # Burn duration (s)

m_structure_s2 = 3000.0     # Dry mass (kg)
m_propellant_s2 = 25000.0   # Fuel mass (kg)
m_payload = 1000.0          # Satellite mass (kg)
thrust_s2 = 350000.0        # Vacuum thrust (N)
burn_time_s2 = 180.0        # Burn duration (s)

cd = 0.3                    # Drag coefficient
area = np.pi * (1.8 ** 2)   # Cross-sectional area (m^2)

# ==========================================
# 3. NUMERICAL INTEGRATION & SIMULATION
# ==========================================
dt = 0.1                    # Time step (seconds)
t_max = 400.0               # Total simulation time (s)

t = 0.0
x, y = 0.0, 0.0             # Positions (m)

# INITIAL VELOCITY INCLUDES EARTH'S ROTATION BOOST!
vx = V_EARTH_ROT            # Initial horizontal velocity from Earth rotation (approx ~320 m/s)
vy = 0.0                    # Initial vertical velocity

mdot_s1 = m_propellant_s1 / burn_time_s1
mdot_s2 = m_propellant_s2 / burn_time_s2

time_hist, alt_hist, vel_hist = [], [], []
q_hist = []  # Dynamic pressure history
mass_hist = []

pitch_start_alt = 1000.0     
pitch_end_alt = 80000.0      

while t < t_max and y >= 0:
    if t < burn_time_s1:
        m_fuel = m_propellant_s1 - mdot_s1 * t
        m_total = m_fuel + m_structure_s1 + m_structure_s2 + m_propellant_s2 + m_payload
        T = thrust_s1
    elif t < (burn_time_s1 + burn_time_s2):
        t_s2 = t - burn_time_s1
        m_fuel = m_propellant_s2 - mdot_s2 * t_s2
        m_total = m_fuel + m_structure_s2 + m_payload
        T = thrust_s2
    else:
        m_total = m_structure_s2 + m_payload
        T = 0.0

    altitude = y
    v = np.sqrt(vx**2 + vy**2)

    # Gravity Turn Logic
    if altitude < pitch_start_alt:
        pitch_angle = np.pi / 2.0  
    elif altitude < pitch_end_alt:
        frac = (altitude - pitch_start_alt) / (pitch_end_alt - pitch_start_alt)
        pitch_angle = (np.pi / 2.0) * (1.0 - 0.85 * frac)  
    else:
        pitch_angle = (np.pi / 2.0) * 0.15  

    # Atmosphere & Aerodynamics
    rho = atmospheric_density(altitude)
    f_drag = 0.5 * rho * (v**2) * cd * area
    q_dynamic = 0.5 * rho * (v**2) / 1000.0  # Dynamic pressure in kPa

    g = G_EARTH * (R_EARTH / (R_EARTH + altitude))**2

    Fx_thrust = T * np.cos(pitch_angle)
    Fy_thrust = T * np.sin(pitch_angle)

    if v > 0:
        Fx_drag = -f_drag * (vx / v)
        Fy_drag = -f_drag * (vy / v)
    else:
        Fx_drag, Fy_drag = 0.0, 0.0

    ax = (Fx_thrust + Fx_drag) / m_total
    ay = (Fy_thrust + Fy_drag) / m_total - g

    vx += ax * dt
    vy += ay * dt
    x += vx * dt
    y += vy * dt
    t += dt

    time_hist.append(t)
    alt_hist.append(y / 1000.0)      
    vel_hist.append(v)               
    q_hist.append(q_dynamic)
    mass_hist.append(m_total / 1000.0)
    # ==========================================
# 4. ADVANCED 4-PANEL DASHBOARD VISUALIZATION
# ==========================================
fig, axs = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle(f'Launch Analysis with Earth Rotation Boost (Lat: {LAUNCH_LATITUDE_DEG}°N)', fontsize=15, fontweight='bold')

# Panel 1: Altitude vs Time
axs[0, 0].plot(time_hist, alt_hist, color='blue', linewidth=2)
axs[0, 0].set_title('Trajectory Altitude')
axs[0, 0].set_ylabel('Altitude (km)')
axs[0, 0].grid(True, linestyle='--', alpha=0.6)

# Panel 2: Velocity vs Time
axs[0, 1].plot(time_hist, vel_hist, color='red', linewidth=2)
axs[0, 1].set_title(f'Flight Velocity (Initial Boost: {V_EARTH_ROT:.1f} m/s)')
axs[0, 1].set_ylabel('Velocity (m/s)')
axs[0, 1].grid(True, linestyle='--', alpha=0.6)

# Panel 3: Dynamic Pressure (Max Q Analysis)
axs[1, 0].plot(time_hist, q_hist, color='orange', linewidth=2)
axs[1, 0].set_title('Dynamic Pressure (Max Q Tracking)')
axs[1, 0].set_xlabel('Time (s)')
axs[1, 0].set_ylabel('Q (kPa)')
axs[1, 0].grid(True, linestyle='--', alpha=0.6)

# Panel 4: Vehicle Mass Decay (Staging Effect)
axs[1, 1].plot(time_hist, mass_hist, color='green', linewidth=2)
axs[1, 1].set_title('Total Vehicle Mass (Staging)')
axs[1, 1].set_xlabel('Time (s)')
axs[1, 1].set_ylabel('Mass (Tonnes)')
axs[1, 1].grid(True, linestyle='--', alpha=0.6)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

plt.savefig('launch_vehicle_dashboard_rotated.png', dpi=300, bbox_inches='tight')

plt.show()