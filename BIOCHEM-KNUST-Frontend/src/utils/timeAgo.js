export function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const secondsAgo = Math.floor((now - date) / 1000);
  
    const intervals = {
      year: 31536000, 
      month: 2592000, 
      week: 604800,   
      day: 86400,     
      hour: 3600,     
      minute: 60,     
    };
  
    for (const interval in intervals) {
      const value = Math.floor(secondsAgo / intervals[interval]);
      if (value >= 1) {
        return `${value} ${interval}${value > 1 ? 's' : ''} ago`;
      }
    }
  
    return "Just now";
  }
  