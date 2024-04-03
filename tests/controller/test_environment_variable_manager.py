import os
from controller.environment_variable_manager import EnvContextManager

def test_without_sat():
    env_var_name = "ENABLE_SENTINEL"
    env_var_value = "False"
    env_var_new_value = "True"
    os.environ[env_var_name] = env_var_value

    with EnvContextManager(ENABLE_SENTINEL=env_var_new_value):
        env_var_context_got_value = os.getenv(env_var_name)
    env_var_after_context_got_value = os.getenv(env_var_name)
    assert env_var_context_got_value == env_var_new_value
    assert env_var_after_context_got_value == env_var_value
