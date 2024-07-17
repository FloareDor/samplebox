type YouTubeEmbedProps = {
	embedUrl: string;
  };
  
  const YouTubeEmbed: React.FC<YouTubeEmbedProps> = ({ embedUrl }) => {
  
	return (
	  <div className="aspect-w-16 aspect-h-9">
		<iframe
            className="w-full h-96"
			src={embedUrl}
            // frameBorder="0"
            allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
		></iframe>
	  </div>
	);
  };
  
  export default YouTubeEmbed;
  