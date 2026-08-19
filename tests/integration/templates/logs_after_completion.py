import time

# The second line is printed immediately before exit so it races the run's
# transition to a terminal status, which is what exercises the CLI's
# post-completion log drain.
print("First log before run completes", flush=True)
time.sleep(2)
print("Second log after run completes", flush=True)
