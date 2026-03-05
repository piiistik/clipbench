from clipbench.core.command_runner.c_runner.c_runner import CRunner

def test_c_runner_echo():
    runner = CRunner()
    
    commands = ["echo 1 2 3" for _ in range(100)]
    
    results = runner.run(commands)
    
    assert len(results) == 100
    for result in results:
        assert result != -1

def test_c_runner_sleep():
    runner = CRunner()
    
    commands = [".\\bin\\sleep.exe 1 1" for _ in range(10)]
    
    results = runner.run(commands)
    
    assert len(results) == 10
    for result in results:
        assert result != -1
