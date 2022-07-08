import std.stdio, std.process, std.parallelism, std.format, std.datetime, std.array, std.regex;
import core.thread.osthread;


alias Callback = void function(string, string);

synchronized class Global {
	//TODO: put error, warning, writef here.  Anything that needs mutexes
}
	
void error(string err) {
	//TODO: set red LED and terminate
}

struct Process {
	string name;
	Callback callback;
	ProcessPipes pipe;

	void process_next_line(string line) {
		if (callback) {
			callback(name, line);
		}
		writef("%s  %16s : %s\n", DateTime().toSimpleString, name, line);//TODO: add timestamp
	}
}
Process[] processes;

void process_lines(Process p) {
	foreach (line; p.pipe.stdout.byLine) {
		p.process_next_line(cast(string)line);
	}
}

/* Starts `command`.
   Output (stdout and stderr) handled as follows:
   - Each line printed to stdout, with a prefix based on `name`
   - run_process doesn't return until it sees a line matching `started`
   - callback will be called for each line
*/
void start_process(string name, string command, Callback callback, string started) {
	Process proc;
	proc.name = name;
	//name2idx[name] = name2idx.length;
	writef("#### Starting %s: %s ####\n", name, command);
	auto cmd = [ "stdbuf", "--output=L" ] ~ command.split();
//	proc.pipe = pipeProcess(cmd, Redirect.stdout);// | Redirect.stderrToStdout);
	proc.pipe = pipeProcess(cmd, Redirect.stdout | Redirect.stderrToStdout);
	proc.callback = callback;
	processes ~= proc;

	// Wait until we see the line indicating it's ready to go
	if (started !is null) {
		foreach (line; proc.pipe.stdout.byLine) {
			proc.process_next_line(cast(string)line);
			if (line.matchFirst(regex(started))) break;
		}
	}
	task!process_lines(proc).executeInNewThread;
}

void jackd_callback(string name, string line) {
	// TODO: detect xruns. If detected, increment a warning count, and set a timer to decrement it
	// The warning flag should be handled by a central function that sets the LED to yellow when it goes from 0 to 1 and
	// sets it to green when it goes from 1 to 0.
}

void main() {
	// TODO: set performance mode
	start_process("performance",
		"./performance_mode",
		null,
		null);
	start_process("jackd",
		"/usr/bin/jackd -P95 -dalsa -r96000 -p128 -n3 -D -Chw:USB -Phw:USB",
		&jackd_callback,
		`^ALSA: use \d periods for playback`);
	start_process("adjmidid",
		"a2jmidid -e",
		null,
		`^port created:.*playback`);
	start_process("guitarix",
		"guitarix --log-terminal",//TODO: change to guitarix -N
		null,
		`buffer size`/*TODO: change to `^Ctrl-C to quit`*/);
		//NOTE: buffer_size shows up in stderr, not stdout
	start_process("midi.py", // TODO: merge all the hardware controllers into this: adc, shutdown.
		"gpio-midi-controller/midi.py",
		null,
		`^ready$`);
	start_process("connect_midi.sh",
		"./connect_midi.sh",
		null,
		`^done$`);
	writef("### All processes started ####\n");

	// `guitarix -N` starts in no-gui mode, and prints "Ctrl-C to quit" to stdout.
	//TODO: look at man guitarix. Got some options that might help make it faster. --help-style, --help-overloada, --help-gtk


	// We've got multiple threads going because it's simpler than setting up non-blocking reads,
	// but this should still be a very low-priority process, so it only gets one core for all of them.
	auto setaffinity = execute(["taskset", "-p", "8", format("%s", getpid)]);//NOTE: assumes we have at least 4 cores
	if (0 != setaffinity.status) {
		error("Failed to set CPU affinity for start");
	}
	//Thread.priority(Thread.PRIORITY_MIN);
}
