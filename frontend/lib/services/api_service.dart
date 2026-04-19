import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';

  static Future<bool> checkConnection() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/'))
          .timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, dynamic>> sendCommand(String text) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/execute"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"text": text}),
      ).timeout(const Duration(seconds: 120));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map) {
          return {
            "result": data["result"]?.toString() ?? "Done",
            "options": data["options"] ?? [],
          };
        }
        return {"result": data.toString(), "options": []};
      }
      return {"result": "Server error: ${response.statusCode}", "options": []};
    } on TimeoutException {
      return {"result": "⏳ Still working...", "options": []};
    } catch (e) {
      return {"result": "Error: ${e.toString()}", "options": []};
    }
  }

  // ✅ ADD THIS — calls backend mic, no Flutter speech package needed
  static Future<Map<String, dynamic>> listenAndExecute() async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/listen"),
        headers: {"Content-Type": "application/json"},
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "heard": data["heard"] ?? "",
          "result": data["result"] ?? "No response",
          "options": data["options"] ?? [],
        };
      }
      return {"heard": "", "result": "Server error", "options": []};
    } on TimeoutException {
      return {"heard": "", "result": "⏳ Listening timed out", "options": []};
    } catch (e) {
      return {"heard": "", "result": "Error: $e", "options": []};
    }
  }
}