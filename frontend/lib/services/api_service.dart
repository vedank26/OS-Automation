import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';

  /// Returns true when the backend health-check endpoint responds 200.
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
        Uri.parse("$baseUrl/smart-execute"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"text": text}),
      ).timeout(const Duration(seconds: 120));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Handle both string and map responses safely
        if (data is Map) {
          return {
            "result": data["result"]?.toString() ?? "Done",
            "options": data["options"] ?? [],
          };
        } else {
          return {
            "result": data.toString(),
            "options": [],
          };
        }
      } else {
        return {
          "result": "Server error: ${response.statusCode}",
          "options": [],
        };
      }
    } on TimeoutException {
      return {
        "result": "⏳ Still working... check VS Code for progress",
        "options": [],
      };
    } catch (e) {
      return {
        "result": "Error: ${e.toString()}",
        "options": [],
      };
    }
  }
}
