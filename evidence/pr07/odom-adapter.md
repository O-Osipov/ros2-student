# Нормализация одометрии и владельцы tf

- Bridge получает `gz.msgs.Odometry` с Gazebo `/model/course_ackermann/odometry`
  и публикует ROS `/vehicle/odom_gz`. Его входные frames в живом опыте:
  `course_ackermann/odom` → `course_ackermann/base_link` (см. `sensors.json`).
- `odom_adapter` принимает только эту пару, проверяет конечность всех числовых
  компонентов pose, twist и обеих covariance. Чужие frames и NaN/∞
  отклоняются без публикации.
- Выход `/vehicle/odom` имеет frames `odom` → `base_link`. Adapter сохраняет
  `header.stamp`, pose, twist и обе covariance. Он же публикует ровно одно
  динамическое ребро `/tf`: `odom` → `base_link` с той же меткой и pose.
- `robot_state_publisher` из ПР06 владеет фиксированными ребрами
  `base_link` → `camera_link`, `lidar_link`, `imu_link` и колёса через
  `/tf_static` с durability `transient_local`. Bridge не публикует `/tf`.
- Тест `test_normalization_preserves_payload_and_stamp` сравнивает stamp,
  pose, twist и covariance до/после; `test_rejects_foreign_frames_and_nonfinite_values`
  проверяет отказ. В живом опыте `scripts/check_pr07_runtime.py` наблюдал
  одну пару `odom` → `base_link` на `/tf` и семь фиксированных связей.
