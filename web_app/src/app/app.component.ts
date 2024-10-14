import { Component, ElementRef, ViewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatButtonModule } from '@angular/material/button';
import { interval, Subscription } from 'rxjs';
import { takeWhile } from 'rxjs/operators';
import { MatTableModule } from '@angular/material/table';

interface Article {
  id: number;
  title: string;
  url: string;
  author: string;
  score: number;
  day: string;
  screenshot_path: string;
  content: any;
  podcast: any;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, MatExpansionModule, MatButtonModule, MatTableModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  @ViewChild('day') day!: ElementRef;
  @ViewChild('data1Day') data1Day!: ElementRef;
  @ViewChild('data2Day') data2Day!: ElementRef;
  @ViewChild('logcontent') logcontent!: ElementRef;
  @ViewChild('articleId') articleId!: ElementRef;
  @ViewChild('podcastArticleId') podcastArticleId!: ElementRef;
  @ViewChild('reviewPodcastArticleId') reviewPodcastArticleId!: ElementRef;
  title = 'web_app';
  private pollingSubscription: Subscription | null = null;
  private lastLogContent: string = '';

  triggerJob(event: Event) {
    event.preventDefault();
    console.log('Scrape button clicked');
    const day = this.day.nativeElement.value;
    console.log(day);
    if (day === '') {
      const today = new Date();
      const formattedToday = today.toISOString().slice(0, 10);
      this.day.nativeElement.value = formattedToday;
    }
    fetch('http://127.0.0.1:5000/trigger-job', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: `python article_scraper.py --day=${day}`,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        this.startPollingLogs('article_scraper', 5000);
      })
      .catch((error) => {
        console.error('Error triggering job:', error);
      });
  }

  startPollingLogs(jobName: string, timeout: number = 3500) {
    this.lastLogContent = '';
    
    // Create log container
    const logContainerHTML = `
      <div id="log-container">
        <h3>Log Output</h3>
        <pre id="log-content" style="background-color: #f0f0f0; padding: 10px; white-space: pre-wrap; max-height: 400px; overflow-y: auto;"></pre>
      </div>
    `;

    const ajaxContent = document.getElementById('ajax-content');
    if (ajaxContent) {
      ajaxContent.innerHTML = logContainerHTML;
    }

    // Make an immediate request
    this.fetchLogs(jobName);
    
    // Then start polling every 3.5 seconds
    this.pollingSubscription = interval(timeout)
      .pipe(
        takeWhile(() => true) // This will keep the polling going until we manually unsubscribe
      )
      .subscribe(() => {
        this.fetchLogs(jobName);
      });
  }

  showData(event: Event) {
    event.preventDefault();
    const selectedDay = this.data1Day.nativeElement.value;

    fetch('http://127.0.0.1:5000/articles')
      .then((response) => response.json())
      .then((articles: Article[]) => {
        const filteredArticles = selectedDay
          ? articles.filter((article) => article.day === selectedDay)
          : articles;

        this.displayArticlesTable(filteredArticles);
      })
      .catch((error) => {
        console.error('Error fetching articles:', error);
      });
  }

  displayArticlesTable(articles: Article[]) {
    const tableHTML = `
      <style>
        .mat-table {
          width: 100%;
        }
        .mat-cell {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        .mat-header-cell {
          background-color: #f2f2f2;
          font-weight: bold;
        }
        .mat-row:nth-child(even) {
          background-color: #f9f9f9;
        }
        .screenshot-img {
          width: 100px;
          max-height: 100px;
          object-fit: contain;
        }
      </style>
      <table mat-table class="mat-table mat-elevation-z8">
        <thead>
          <tr class="mat-header-row">
            <th class="mat-cell mat-header-cell">ID</th>
            <th class="mat-cell mat-header-cell">Title</th>
            <th class="mat-cell mat-header-cell">Author</th>
            <th class="mat-cell mat-header-cell">Score</th>
            <th class="mat-cell mat-header-cell">Day</th>
            <th class="mat-cell mat-header-cell">Screenshot</th>
          </tr>
        </thead>
        <tbody>
          ${articles
            .map(
              (article) => `
            <tr class="mat-row">
              <td class="mat-cell"><a href="http://127.0.0.1:5000/article/${article.id}" target="_blank">${article.id}</a></td>
              <td class="mat-cell"><a href="${article.url}" target="_blank">${article.title}</a></td>
              <td class="mat-cell">${article.author}</td>
              <td class="mat-cell">${article.score}</td>
              <td class="mat-cell">${article.day}</td>
              <td class="mat-cell">
                ${article.screenshot_path ? 
                  `<img src="http://127.0.0.1:5000/screenshot?id=${article.id}" alt="Screenshot" class="screenshot-img">` : 
                  'No screenshot available'}
              </td>
            </tr>
          `
            )
            .join('')}
        </tbody>
      </table>
    `;

    const ajaxContent = document.getElementById('ajax-content');
    if (ajaxContent) {
      ajaxContent.innerHTML = tableHTML;
    }
  }

  fetchLogs(jobName: string) {
    fetch(`http://127.0.0.1:5000/logs/${jobName}`)
      .then((response) => response.json())
      .then((data) => {
        const currentLogContent = data.lines.join('');
        if (currentLogContent !== this.lastLogContent) {
          console.log(data);
          const logContentElement = document.getElementById('log-content');
          if (logContentElement) {
            logContentElement.textContent = currentLogContent;
            // Scroll to the bottom of the log content
            logContentElement.scrollTop = logContentElement.scrollHeight;
          }
          this.lastLogContent = currentLogContent;
        } else {
          console.log('No new log updates');
          this.stopPolling();
        }
      })
      .catch((error) => {
        console.error('Error fetching logs:', error);
        this.stopPolling();
      });
  }

  stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  runAugmentation(event: Event) {
    event.preventDefault();
    console.log('Run augmentation button clicked');
    const day = this.data2Day.nativeElement.value;
    console.log(day);
    if (day === '') {
      const today = new Date();
      const formattedToday = today.toISOString().slice(0, 10);
      this.data2Day.nativeElement.value = formattedToday;
    }
    fetch('http://127.0.0.1:5000/trigger-job', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: `python agents/screenshot.py --day=${day}`,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        this.startPollingLogs('screenshot_agent', 9000);
      })
      .catch((error) => {
        console.error('Error triggering job:', error);
      });
  }

  showData2(event: Event) {
    event.preventDefault();
    const articleId = this.articleId.nativeElement.value;

    fetch(`http://127.0.0.1:5000/article/${articleId}`)
      .then((response) => response.json())
      .then((article: Article) => {
        // Create a container div for the JSON display
        const jsonContainer = document.createElement('div');
        jsonContainer.id = 'json-container';
        jsonContainer.style.cssText = `
          background-color: #f0f0f0;
          padding: 20px;
          border-radius: 5px;
          font-family: monospace;
          white-space: pre-wrap;
          word-wrap: break-word;
          max-height: 500px;
          overflow-y: auto;
        `;

        // Convert the article object to a formatted JSON string
        const formattedJson = JSON.stringify(JSON.parse(article.content), null, 2);
        console.log(JSON.stringify(formattedJson, null, 2));

        // Set the formatted JSON as the content of the container
        jsonContainer.textContent = formattedJson;

        // Clear previous content and append the new JSON container
        const ajaxContent = document.getElementById('ajax-content');
        if (ajaxContent) {
          ajaxContent.innerHTML = '';
          ajaxContent.appendChild(jsonContainer);
        }
      })
      .catch((error) => {
        console.error('Error fetching article:', error);
      });
  }

  createPodcast(event: Event) {
    event.preventDefault();
    console.log('Create podcast button clicked');
    const articleId = this.podcastArticleId.nativeElement.value;
    fetch('http://127.0.0.1:5000/trigger-job', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        command: `python agents/podcast_generator.py --id=${articleId}`,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        this.startPollingLogs('podcast_generator_agent', 15000);
      })
      .catch((error) => {
        console.error('Error triggering job:', error);
      });
  }

  reviewPodcast(event: Event) {
    event.preventDefault();
    console.log('Review podcast button clicked');
    const articleId = this.reviewPodcastArticleId.nativeElement.value;
    console.log(articleId);
    fetch(`http://127.0.0.1:5000/article/${articleId}`)
      .then((response) => response.json())
      .then((article: Article) => {
        console.log(article);
        const jsonContainer = document.createElement('div');
        jsonContainer.id = 'json-container';
        jsonContainer.style.cssText = `
          background-color: #f0f0f0;
          padding: 20px;
          border-radius: 5px;
          font-family: monospace;
          white-space: pre-wrap;
          word-wrap: break-word;
          max-height: 500px;
          overflow-y: auto;
        `;

        const formattedJson = article.podcast;

        jsonContainer.textContent = formattedJson;

        const ajaxContent = document.getElementById('ajax-content');
        if (ajaxContent) {
          ajaxContent.innerHTML = '';
          ajaxContent.appendChild(jsonContainer);
        }
      })
      .catch((error) => {
        console.error('Error fetching article:', error);
      });
  }
}
