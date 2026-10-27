import time

class BenchmarkTimes:
    """
    A class to benchmark and record various time intervals.
    """
    def __init__(self):
        """
        Initialize all time attributes to None.
        """
        self.start_time = None
        self.end_time = None
        self.req_start_time = None
        self.req_end_time = None
        self.post_processing_start_time = None
        self.post_processing_end_time = None
        self.login_start_time = None
        self.login_end_time = None
        self.output_write_start_time = None
        self.output_write_end_time = None

    def set_benchmark_time(self, key):
        """
        Set the current time to the attribute specified by key.
        
        Args:
            key (str): The attribute name to set the current time.
        """
        setattr(self, key, time.time())

    def set_start_time(self):
        """
        Set the start time to the current time.
        """
        self.set_benchmark_time("start_time")
    
    def set_end_time(self):
        """
        Set the end time to the current time.
        """
        self.set_benchmark_time("end_time")

    def set_req_start_time(self):
        """
        Set the request start time to the current time.
        """
        self.set_benchmark_time("req_start_time")
    
    def set_req_end_time(self):
        """
        Set the request end time to the current time.
        """
        self.set_benchmark_time("req_end_time")
    
    def set_post_processing_start_time(self):
        """
        Set the post-processing start time to the current time.
        """
        self.set_benchmark_time("post_processing_start_time")
    
    def set_post_processing_end_time(self):
        """
        Set the post-processing end time to the current time.
        """
        self.set_benchmark_time("post_processing_end_time")
    
    def set_login_start_time(self):
        """
        Set the login start time to the current time.
        """
        self.set_benchmark_time("login_start_time")
    
    def set_login_end_time(self):
        """
        Set the login end time to the current time.
        """
        self.set_benchmark_time("login_end_time")
    
    def set_output_write_start_time(self):
        """
        Set the output write start time to the current time.
        """
        self.set_benchmark_time("output_write_start_time")

    def set_output_write_end_time(self):
        """
        Set the output write end time to the current time.
        """
        self.set_benchmark_time("output_write_end_time")

    def __str__(self):
        """
        Print the benchmark results for total time, login time, request time, and post-processing time.
        """
        result = "----- Benchmark results -----\n"
        
        if all([self.login_start_time, self.login_end_time]):
            result += f"Login time: {round(self.login_end_time - self.login_start_time, 1)}s\n"
        else:
            result += "Login time: N/A\n"
        
        if all([self.req_start_time, self.req_end_time]):
            result += f"Request time: {round(self.req_end_time - self.req_start_time, 1)}s\n"
        else:
            result += "Request time: N/A\n"

        if all([self.post_processing_start_time, self.post_processing_end_time]):
            result += f"Post processing time: {round(self.post_processing_end_time - self.post_processing_start_time, 1)}s\n"
        else:
            result += "Post processing time: N/A\n"
        
        if all([self.output_write_start_time, self.output_write_end_time]):
            result += f"Output write time: {round(self.output_write_end_time - self.output_write_start_time, 1)}s\n"
        else:
            result += "Output write time: N/A\n"
    
        if all([self.start_time, self.end_time]):
            result += f"Total time: {round(self.end_time - self.start_time, 1)}s\n"
        else:
            result += "Total time: N/A\n"

        return result

    def print_results(self):
        print(str(self))