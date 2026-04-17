import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;

void main() {
  runApp(const AIOperatingSystem());
}

// ─── App Root ───
class AIOperatingSystem extends StatelessWidget {
  const AIOperatingSystem({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI OS v1.0',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0A0E1A),
      ),
      home: const OSInterface(),
    );
  }
}

// ─── Color Constants ───
class C {
  static const bg = Color(0xFF0A0E1A);
  static const surface = Color(0xFF111827);
  static const border = Color(0xFF1E293B);
  static const neon = Color(0xFF00D4FF);
  static const neonDim = Color(0xFF0891B2);
  static const ai = Color(0xFF60A5FA);
  static const sys = Color(0xFFFBBF24);
  static const ok = Color(0xFF34D399);
  static const err = Color(0xFFEF4444);
  static const txt = Color(0xFFE2E8F0);
  static const dim = Color(0xFF64748B);
  static const inputBg = Color(0xFF0F172A);
}

// ─── Log Entry Model ───
class LogEntry {
  final String tag; // AI, SYS, SUCCESS, ERROR, CMD, INFO
  final String message;
  final DateTime time;
  LogEntry(this.tag, this.message) : time = DateTime.now();

  Color get color {
    switch (tag) {
      case 'AI': return C.ai;
      case 'SYS': return C.sys;
      case 'SUCCESS': return C.ok;
      case 'ERROR': return C.err;
      case 'CMD': return C.neon;
      case 'INFO': return C.dim;
      default: return C.txt;
    }
  }
}

// ─── Parsed Command Model ───
class ParsedCommand {
  final String action;
  final String target;
  ParsedCommand(this.action, this.target);
}

// ─── Main OS Interface ───
class OSInterface extends StatefulWidget {
  const OSInterface({super.key});
  @override
  State<OSInterface> createState() => _OSInterfaceState();
}

class _OSInterfaceState extends State<OSInterface> with TickerProviderStateMixin {
  final TextEditingController _cmdCtrl = TextEditingController();
  final FocusNode _focusNode = FocusNode();
  final ScrollController _scrollCtrl = ScrollController();
  final List<LogEntry> _logs = [];
  bool _isProcessing = false;
  String _status = 'Ready';
  ParsedCommand? _parsed;
  late AnimationController _glowCtrl;
  late Animation<double> _glowAnim;
  int _cmdCount = 0;

  @override
  void initState() {
    super.initState();
    _glowCtrl = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    _glowAnim = Tween(begin: 0.3, end: 1.0).animate(
      CurvedAnimation(parent: _glowCtrl, curve: Curves.easeInOut),
    );
    _addLog('INFO', 'AI Operating System initialized.');
    _addLog('INFO', 'Type a command and press Enter.');
  }

  @override
  void dispose() {
    _glowCtrl.dispose();
    _cmdCtrl.dispose();
    _focusNode.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _addLog(String tag, String msg) {
    setState(() => _logs.add(LogEntry(tag, msg)));
    Future.delayed(const Duration(milliseconds: 50), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  ParsedCommand _parseCommand(String cmd) {
    final lower = cmd.toLowerCase().trim();
    if (lower.startsWith('create folder') || lower.startsWith('create a folder')) {
      final name = lower.replaceAll(RegExp(r'create\s+a?\s*folder\s*(named|called)?\s*'), '').trim();
      return ParsedCommand('create_folder', name.isEmpty ? 'NewFolder' : name);
    } else if (lower.startsWith('open ')) {
      return ParsedCommand('open_app', lower.replaceFirst('open ', '').trim());
    } else if (lower.startsWith('search ')) {
      return ParsedCommand('search_web', lower.replaceFirst('search ', '').trim());
    } else if (lower.contains('shutdown')) {
      return ParsedCommand('shutdown', 'system');
    } else if (lower.contains('restart')) {
      return ParsedCommand('restart', 'system');
    } else if (lower.contains('play music') || lower.contains('play song')) {
      return ParsedCommand('play_media', 'music');
    } else if (lower.startsWith('create react app')) {
      final name = lower.replaceAll(RegExp(r'create\s+react\s+app\s*(named|called)?\s*'), '').trim();
      return ParsedCommand('create_react_app', name.isEmpty ? 'my-app' : name);
    }
    return ParsedCommand('execute', cmd);
  }

  Future<void> _executeCommand() async {
    final cmd = _cmdCtrl.text.trim();
    if (cmd.isEmpty || _isProcessing) return;

    setState(() {
      _isProcessing = true;
      _status = 'Processing';
      _cmdCount++;
      _parsed = _parseCommand(cmd);
    });

    _addLog('CMD', '\$ $cmd');
    _cmdCtrl.clear();

    // Step 1: AI interpreting
    _addLog('AI', 'Interpreting command...');
    await Future.delayed(const Duration(milliseconds: 400));

    _addLog('AI', 'Action: ${_parsed!.action} | Target: ${_parsed!.target}');
    await Future.delayed(const Duration(milliseconds: 300));

    // Step 2: System executing
    _addLog('SYS', 'Executing ${_parsed!.action}...');
    setState(() => _status = 'Executing');
    await Future.delayed(const Duration(milliseconds: 200));

    // Step 3: Send to backend
    try {
      final response = await http.post(
        Uri.parse("http://127.0.0.1:8000/execute"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"text": cmd}),
      ).timeout(const Duration(seconds: 10));

      final data = jsonDecode(response.body);
      final result = data["result"] ?? "No response";

      if (result.toLowerCase().contains('not recognized') ||
          result.toLowerCase().contains('error')) {
        _addLog('ERROR', result);
      } else {
        _addLog('SUCCESS', result);
      }
    } catch (e) {
      _addLog('ERROR', 'Connection failed: ${e.toString().split(':').first}');
    }

    setState(() {
      _isProcessing = false;
      _status = 'Ready';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: C.bg,
      body: Column(
        children: [
          _buildStatusBar(),
          Expanded(
            child: Row(
              children: [
                // Main terminal area
                Expanded(flex: 3, child: _buildTerminal()),
                // Side panel
                Container(width: 1, color: C.border),
                Expanded(flex: 1, child: _buildSidePanel()),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: _buildMicButton(),
    );
  }

  // ─── Status Bar ───
  Widget _buildStatusBar() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        color: C.surface,
        border: Border(bottom: BorderSide(color: C.border, width: 1)),
        boxShadow: [
          BoxShadow(color: C.neon.withOpacity(0.05), blurRadius: 10),
        ],
      ),
      child: Row(
        children: [
          // Logo
          Container(
            width: 8, height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _status == 'Ready' ? C.ok : C.sys,
              boxShadow: [
                BoxShadow(
                  color: (_status == 'Ready' ? C.ok : C.sys).withOpacity(0.6),
                  blurRadius: 6,
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Text(
            'AI OS v1.0',
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 13,
              color: C.neon, fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(width: 20),
          _statusChip('Connected', C.ok),
          const SizedBox(width: 12),
          _statusChip(_status, _status == 'Ready' ? C.ok : C.sys),
          const Spacer(),
          Text(
            'Commands: $_cmdCount',
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 11, color: C.dim,
            ),
          ),
          const SizedBox(width: 16),
          Text(
            '${DateTime.now().hour.toString().padLeft(2, '0')}:${DateTime.now().minute.toString().padLeft(2, '0')}',
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 11, color: C.dim,
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        border: Border.all(color: color.withOpacity(0.4)),
        borderRadius: BorderRadius.circular(3),
        color: color.withOpacity(0.08),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'monospace', fontSize: 10,
          color: color, fontWeight: FontWeight.w600,
          letterSpacing: 0.8,
        ),
      ),
    );
  }

  // ─── Terminal ───
  Widget _buildTerminal() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Terminal header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: C.surface.withOpacity(0.5),
          child: Row(
            children: [
              Icon(Icons.terminal, size: 14, color: C.neonDim),
              const SizedBox(width: 8),
              Text(
                'TERMINAL',
                style: TextStyle(
                  fontFamily: 'monospace', fontSize: 11,
                  color: C.dim, letterSpacing: 2,
                ),
              ),
            ],
          ),
        ),
        // Log output
        Expanded(
          child: Container(
            color: C.bg,
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(16),
              itemCount: _logs.length,
              itemBuilder: (ctx, i) => _buildLogLine(_logs[i]),
            ),
          ),
        ),
        // Command input
        _buildCommandInput(),
      ],
    );
  }

  Widget _buildLogLine(LogEntry log) {
    final timeStr =
        '${log.time.hour.toString().padLeft(2, '0')}:'
        '${log.time.minute.toString().padLeft(2, '0')}:'
        '${log.time.second.toString().padLeft(2, '0')}';

    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$timeStr ',
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 12, color: C.dim.withOpacity(0.5),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: log.color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(2),
            ),
            child: Text(
              '[${log.tag}]',
              style: TextStyle(
                fontFamily: 'monospace', fontSize: 12,
                color: log.color, fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              log.message,
              style: TextStyle(
                fontFamily: 'monospace', fontSize: 12.5, color: C.txt,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCommandInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: C.inputBg,
        border: Border(top: BorderSide(color: C.neon.withOpacity(0.2))),
      ),
      child: Row(
        children: [
          Text(
            '❯ ',
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 16,
              color: C.neon, fontWeight: FontWeight.bold,
            ),
          ),
          Expanded(
            child: TextField(
              controller: _cmdCtrl,
              focusNode: _focusNode,
              style: TextStyle(
                fontFamily: 'monospace', fontSize: 14, color: C.txt,
              ),
              cursorColor: C.neon,
              cursorWidth: 8,
              cursorHeight: 16,
              decoration: InputDecoration(
                hintText: _isProcessing ? 'Processing...' : 'Enter command...',
                hintStyle: TextStyle(
                  fontFamily: 'monospace', fontSize: 14, color: C.dim.withOpacity(0.5),
                ),
                border: InputBorder.none,
                isDense: true,
                contentPadding: EdgeInsets.zero,
              ),
              enabled: !_isProcessing,
              onSubmitted: (_) => _executeCommand(),
            ),
          ),
          if (_isProcessing)
            SizedBox(
              width: 16, height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2, color: C.neon,
              ),
            )
          else
            InkWell(
              onTap: _executeCommand,
              child: Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  border: Border.all(color: C.neon.withOpacity(0.3)),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Icon(Icons.play_arrow, size: 16, color: C.neon),
              ),
            ),
        ],
      ),
    );
  }

  // ─── Side Panel ───
  Widget _buildSidePanel() {
    return Container(
      color: C.surface.withOpacity(0.3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Panel header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: C.surface.withOpacity(0.5),
            child: Row(
              children: [
                Icon(Icons.psychology, size: 14, color: C.ai),
                const SizedBox(width: 8),
                Text(
                  'AI INTERPRETER',
                  style: TextStyle(
                    fontFamily: 'monospace', fontSize: 11,
                    color: C.dim, letterSpacing: 2,
                  ),
                ),
              ],
            ),
          ),
          // Parsed command display
          if (_parsed != null)
            Container(
              margin: const EdgeInsets.all(12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: C.bg,
                border: Border.all(color: C.neon.withOpacity(0.15)),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _infoRow('Action', _parsed!.action, C.ai),
                  const SizedBox(height: 8),
                  _infoRow('Target', _parsed!.target, C.ok),
                ],
              ),
            )
          else
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Awaiting command...',
                style: TextStyle(
                  fontFamily: 'monospace', fontSize: 11, color: C.dim,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
          const Divider(color: C.border, height: 1),
          // Quick commands
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: C.surface.withOpacity(0.5),
            child: Text(
              'QUICK COMMANDS',
              style: TextStyle(
                fontFamily: 'monospace', fontSize: 11,
                color: C.dim, letterSpacing: 2,
              ),
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(8),
              children: [
                _quickCmd('open notepad'),
                _quickCmd('open chrome'),
                _quickCmd('open vscode'),
                _quickCmd('create folder Test'),
                _quickCmd('search flutter'),
                _quickCmd('open explorer'),
                _quickCmd('open task manager'),
              ],
            ),
          ),
          // System info footer
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: C.border)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _infoRow('Backend', '127.0.0.1:8000', C.ok),
                const SizedBox(height: 4),
                _infoRow('Status', _isProcessing ? 'Busy' : 'Idle', _isProcessing ? C.sys : C.ok),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value, Color valueColor) {
    return Row(
      children: [
        Text(
          '$label: ',
          style: TextStyle(
            fontFamily: 'monospace', fontSize: 11, color: C.dim,
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontFamily: 'monospace', fontSize: 11,
              color: valueColor, fontWeight: FontWeight.w600,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _quickCmd(String cmd) {
    return InkWell(
      onTap: () {
        _cmdCtrl.text = cmd;
        _executeCommand();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        margin: const EdgeInsets.only(bottom: 4),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(3),
          border: Border.all(color: C.border),
        ),
        child: Row(
          children: [
            Text('❯ ', style: TextStyle(fontFamily: 'monospace', fontSize: 11, color: C.neonDim)),
            Text(
              cmd,
              style: TextStyle(fontFamily: 'monospace', fontSize: 11, color: C.txt.withOpacity(0.7)),
            ),
          ],
        ),
      ),
    );
  }

  // ─── Mic Button ───
  Widget _buildMicButton() {
    return AnimatedBuilder(
      animation: _glowAnim,
      builder: (ctx, child) {
        return Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: C.neon.withOpacity(0.3 * _glowAnim.value),
                blurRadius: 20 * _glowAnim.value,
                spreadRadius: 2 * _glowAnim.value,
              ),
            ],
          ),
          child: FloatingActionButton(
            onPressed: () {
              _addLog('INFO', 'Voice input coming soon...');
            },
            backgroundColor: C.surface,
            shape: CircleBorder(side: BorderSide(color: C.neon.withOpacity(0.5))),
            child: Icon(Icons.mic, color: C.neon, size: 24),
          ),
        );
      },
    );
  }
}