include(boards/mpconfigboard_esp32s3_common.cmake)

list(APPEND SDKCONFIG_DEFAULTS
    boards/sdkconfig.flash_qio_80m
    boards/sdkconfig.csi
    boards/sdkconfig.ble_single_connection
)

set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/../ESPIDE/manifest.py)
