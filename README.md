---


---

<p>This open project is made available under the following terms and conditions:</p>
<ul>
<li><strong>Academic and Technical Exchange Usage Only:</strong> This project is intended solely for academic and technical exchange purposes. It is provided to facilitate learning, research, and collaboration within academic and technical communities.</li>
<li><strong>Non-Commercial Usage:</strong> The materials, data, code, and any associated resources provided within this project are not to be used for commercial purposes. Commercial usage, including but not limited to reproduction, distribution, or exploitation for financial gain, is strictly prohibited without explicit authorization.</li>
<li><strong>Ownership of Original Data and Articles:</strong> The original data and articles included in this project remain the intellectual property of their respective authors. Any use of these materials beyond the scope of this license may require separate permission from the copyright holders.</li>
<li><strong>Modification and Redistribution:</strong> Users are permitted to modify and redistribute the materials within this project for academic and technical purposes only, provided that proper attribution is given to the original authors and that the modified versions are distributed under the same terms as this license.</li>
<li><strong>No Warranty:</strong> This project is provided “as is,” without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. The authors of this project disclaim any liability for damages resulting from the use or misuse of the provided materials.</li>
</ul>
<p>By accessing or using this project, you agree to abide by the terms of this license. If you do not agree with these terms, you are not permitted to access or use the materials within this project.</p>
<hr>
<h1 id="multilingual-web-scraping-and-translation-integration-for-wordpress">Multilingual Web Scraping and Translation Integration for WordPress</h1>
<p>This project orchestrates a comprehensive workflow encompassing web scraping from diverse sources, subsequent translation into English, Traditional Chinese, and Simplified Chinese, and finally, publishing the content onto a WordPress website hosted at <a href="https://ozeasy.com/">https://ozeasy.com</a>. The integration seamlessly merges various technologies including WordPress, MariaDB, Google Gemini API, OpenAI API, Google Translate API, and SEO optimization techniques. A Linux Jumpbox serves as the operational hub, executing a Python cronjob to scrape posts and transmit them to WordPress using RestAPI.</p>
<h2 id="key-features">Key Features</h2>
<ul>
<li>
<p><strong>Web Scraping:</strong> Automated scraping of content from multiple sources.</p>
</li>
<li>
<p><strong>Multilingual Translation:</strong> Translates scraped content into English, Traditional Chinese, and Simplified Chinese for broader audience reach.</p>
</li>
<li>
<p><strong>WordPress Integration:</strong> Publishes translated content onto a WordPress website, ensuring timely updates and engagement.</p>
</li>
<li>
<p><strong>API Integration:</strong> Utilizes Google Gemini API, OpenAI API, and Google Translate API for various functionalities such as language translation and content optimization.</p>
</li>
<li>
<p><strong>SEO Optimization:</strong> Implements techniques to enhance search engine visibility and improve website ranking.</p>
</li>
<li>
<p><strong>Automated Cronjob:</strong> A Python cronjob running on a Linux Jumpbox automates the scraping and publishing process, ensuring consistency and efficiency.</p>
</li>
</ul>
<h2 id="technologies-used">Technologies Used</h2>
<ul>
<li>WordPress</li>
<li>MariaDB</li>
<li>Google Gemini API</li>
<li>OpenAI API</li>
<li>Google Translate API</li>
<li>Linux Jumpbox</li>
<li>Python</li>
</ul>
<h2 id="usage">Usage</h2>
<ol>
<li>Configure the necessary APIs and credentials required for translation and other functionalities.</li>
<li>Set up a Linux Jumpbox with the required dependencies and permissions.</li>
<li>Clone this repository onto the Jumpbox.</li>
<li>Configure the Python cronjob to run at specified intervals for scraping and publishing content.</li>
<li>Monitor the process and troubleshoot any issues that may arise.</li>
</ol>
<h2 id="prerequisites">Prerequisites</h2>
<ul>
<li>Access to WordPress website with RestAPI enabled.</li>
<li>Proper setup and configuration of MariaDB, Google Gemini API, OpenAI API, and Google Translate API.</li>
<li>Linux environment for hosting the Jumpbox and executing the crontab job.</li>
</ul>
<h2 id="section"><img src="https://github.com/albert-projects/python-wp-autoposts/blob/master/screenshot.png" alt="Screenshot"></h2>
<p>python-wp-autoposts<br>
Albert Kwan<br>
April 2024</p>

