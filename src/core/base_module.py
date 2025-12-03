class BaseModule:
    def success(self, message, data=None):
        return {
            "success": True,
            "message": message,
            "data": data
        }

    def failure(self, message, data=None):
        return {
            "success": False,
            "message": message,
            "data": data
        }
