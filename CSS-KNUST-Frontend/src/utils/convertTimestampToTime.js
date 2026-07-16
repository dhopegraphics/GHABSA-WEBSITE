const convertTimestampToTime =()=>{
    const convertTimestamp = (timestamp) => {
        const date = new Date(timestamp?.seconds * 1000 + timestamp?.nanoseconds / 1000000);
      
        let hours = date.getHours();
        const minutes = date.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
      
        hours = hours % 12;
        hours = hours ? hours : 12;
        const minutesStr = minutes < 10 ? `0${minutes}` : minutes;
      
        const formattedTime = `${hours}:${minutesStr} ${ampm}`;
        return formattedTime;
      };
      

      return {convertTimestamp}
      
}

export default convertTimestampToTime