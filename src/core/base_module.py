class BaseModule:
    def success(self, message, result=None):
        return {
            "success": True,
            "message": message,
            "result": result
        }

    def failure(self, message, error=None):
        return {
            "success": False,
            "message": message,
            "error": error
        }
