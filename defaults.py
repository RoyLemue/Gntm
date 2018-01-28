from mezzanine.conf import register_setting

register_setting(
    name="GNTM_LOCKED",
    label="Locked",
    description="Lock/Unlock Gntm Transaction System",
    editable=True,
    default=False,
)