#!/usr/bin/env python3
"""
format_output.py - Review Output Formatter

Compiles analysis data and reviews into formatted markdown.
Uses templates from assets/ and generates review-output.md.

Usage:
    # Format using full report template
    python format_output.py \\
      --base main \\
      --compare feature/xyz \\
      --analysis analysis.json \\
      --reviews reviews.json \\
      --template assets/report.md \\
      --output review-output.md

    # Format summary only
    python format_output.py \\
      --analysis analysis.json \\
      --template assets/summary.md \\
      --output summary.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class OutputFormatter:
    """Code review output formatter."""
    
    SEVERITY_EMOJIS = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'info': 'ℹ️'
    }
    
    CATEGORY_EMOJIS = {
        'security': '🔒',
        'performance': '⚡',
        'testing': '🧪',
        'documentation': '📝',
        'code quality': '⚙️',
        'architecture': '🏗️'
    }
    
    def __init__(
        self,
        template_path: str,
        output_format: str = 'bitbucket'
    ):
        self.template_path = Path(template_path)
        self.output_format = output_format
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(self.template_path, 'r') as f:
            self.template = f.read()
    
    def load_json(self, filepath: str) -> Dict:
        """Loads a JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def format_file_list(
        self,
        files: List[Dict],
        status_filter: Optional[str] = None
    ) -> str:
        """Formats a list of files."""
        filtered = files
        if status_filter:
            filtered = [f for f in files if f['status'] == status_filter]

        if not filtered:
            return "_(none)_"
        
        output = []
        for f in filtered:
            status_icon = {
                'M': '📝',
                'A': '✨',
                'D': '🗑️',
                'R': '📦'
            }.get(f['status'], '❓')
            
            output.append(
                f"- {status_icon} `{f['path']}` "
                f"(+{f['additions']}, -{f['deletions']})"
            )
        
        return '\n'.join(output)
    
    def format_features_list(self, features: List[Dict]) -> str:
        """Formats the list of identified features."""
        if not features:
            return "_(no features identified)_"

        output = []
        for i, feature in enumerate(features, 1):
            impact_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(feature['impact'], '❓')

            risk_emoji = {
                'high': '⚠️',
                'medium': '⚡',
                'low': '✅'
            }.get(feature['risk'], '❓')

            output.append(f"**Feature #{i}: {feature['name']}**")
            output.append(f"- **Impact:** {impact_emoji} {feature['impact'].title()}")
            output.append(f"- **Risk:** {risk_emoji} {feature['risk'].title()}")
            output.append(f"- **Files:** {len(feature['files'])}")
            output.append(f"- **Description:** {feature['description']}")

            # List files
            for fp in feature['files'][:3]:
                output.append(f"  - `{fp}`")
            if len(feature['files']) > 3:
                output.append(f"  - _(and {len(feature['files']) - 3} more)_")
            
            output.append("")
        
        return '\n'.join(output)
    
    def format_alerts_list(self, alerts: List[Dict]) -> str:
        """Formats the list of alerts."""
        if not alerts:
            return "✅ No automatic alerts detected."
        
        output = []
        by_severity = {}
        for alert in alerts:
            severity = alert['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(alert)
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity not in by_severity:
                continue
            
            alerts_list = by_severity[severity]
            emoji = self.SEVERITY_EMOJIS[severity]
            
            output.append(f"### {emoji} {severity.upper()}: {len(alerts_list)} issues")
            output.append("")
            
            for alert in alerts_list[:5]:  # Show up to 5 per severity
                output.append(
                    f"- **{alert['file']}:{alert['line']}** - {alert['message']}"
                )
                if alert.get('context'):
                    output.append(f"  ```python\n  {alert['context']}\n  ```")
            
            if len(alerts_list) > 5:
                output.append(f"- _(and {len(alerts_list) - 5} more issues)_")
            
            output.append("")
        
        return '\n'.join(output)
    
    def format_complexity_table(self, files: List[Dict]) -> str:
        """Formats the complexity table."""
        python_files = [f for f in files if f['path'].endswith('.py')]

        if not python_files:
            return "_(no Python files)_"

        # Sort by total changes (desc)
        sorted_files = sorted(
            python_files,
            key=lambda f: f['additions'] + f['deletions'],
            reverse=True
        )
        
        rows = []
        for f in sorted_files[:10]:  # Top 10 files
            total = f['additions'] + f['deletions']
            complexity_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'very_high': '🔴'
            }.get(f['complexity'], '❓')
            
            rows.append(
                f"| `{f['path']}` | +{f['additions']} -{f['deletions']} | "
                f"{complexity_emoji} {f['complexity'].replace('_', ' ').title()} |"
            )
        
        return '\n'.join(rows)
    
    def format_authors_list(self, base: str, compare: str) -> str:
        """Formats the list of authors (via git log)."""
        import subprocess

        try:
            result = subprocess.run(
                ['git', 'log', f'{base}..{compare}', '--format=%an'],
                capture_output=True,
                text=True,
                check=True
            )
            
            authors = result.stdout.strip().split('\n')
            author_counts = {}
            for author in authors:
                author_counts[author] = author_counts.get(author, 0) + 1
            
            sorted_authors = sorted(
                author_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            output = []
            for author, count in sorted_authors:
                output.append(f"- **{author}**: {count} commit(s)")
            
            return '\n'.join(output)
        
        except subprocess.CalledProcessError:
            return "_(could not retrieve authors)_"

    def format_commits_count(self, base: str, compare: str) -> int:
        """Counts commits between branches."""
        import subprocess
        
        try:
            result = subprocess.run(
                ['git', 'log', f'{base}..{compare}', '--oneline'],
                capture_output=True,
                text=True,
                check=True
            )
            return len(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError:
            return 0
    
    def fill_summary_template(
        self,
        analysis: Dict,
        base: str,
        compare: str
    ) -> str:
        """Fills the summary template (assets/summary.md)."""
        stats = analysis['stats']
        files = analysis['files']
        features = analysis['features']
        alerts = analysis['alerts']
        metrics = analysis['metrics']

        # Separate Python files by status
        python_files = [f for f in files if f['path'].endswith('.py')]
        python_modified = [f for f in python_files if f['status'] == 'M']
        python_added = [f for f in python_files if f['status'] == 'A']
        python_deleted = [f for f in python_files if f['status'] == 'D']
        python_renamed = [f for f in python_files if f['status'] == 'R']
        
        other_files = [f for f in files if not f['path'].endswith('.py')]
        
        # Commits
        total_commits = self.format_commits_count(base, compare)

        # File prioritization
        high_priority = [
            f for f in python_files
            if f['status'] == 'A' or 'auth' in f['path'].lower() or 'schema' in f['path'].lower()
        ]
        medium_priority = [
            f for f in python_files
            if f not in high_priority and ('model' in f['path'].lower() or 'api' in f['path'].lower())
        ]
        low_priority = [
            f for f in python_files
            if f not in high_priority and f not in medium_priority
        ]
        
        # Fill placeholders
        replacements = {
            '{base_branch}': base,
            '{compare_branch}': compare,
            '{review_date}': datetime.now().strftime('%Y-%m-%d %H:%M'),
            '{total_commits}': str(total_commits),
            '{total_files}': str(stats['total_files']),
            '{python_files}': str(stats['python_files']),
            '{lines_added}': str(stats['additions']),
            '{lines_removed}': str(stats['deletions']),
            '{net_change}': f"{stats['net_change']:+d}",
            
            '{python_modified_count}': str(len(python_modified)),
            '{python_modified_list}': self.format_file_list(python_modified),
            
            '{python_added_count}': str(len(python_added)),
            '{python_added_list}': self.format_file_list(python_added),
            
            '{python_deleted_count}': str(len(python_deleted)),
            '{python_deleted_list}': self.format_file_list(python_deleted),
            
            '{python_renamed_count}': str(len(python_renamed)),
            '{python_renamed_list}': self.format_file_list(python_renamed),
            
            '{other_files_count}': str(len(other_files)),
            '{other_files_list}': self.format_file_list(other_files),
            
            '{features_list}': self.format_features_list(features),
            '{authors_list}': self.format_authors_list(base, compare),
            '{complexity_table}': self.format_complexity_table(files),
            '{preliminary_alerts}': self.format_alerts_list(alerts),
            
            '{high_priority_files}': self.format_file_list(high_priority) if high_priority else "_(none)_",
            '{medium_priority_files}': self.format_file_list(medium_priority) if medium_priority else "_(none)_",
            '{low_priority_files}': self.format_file_list(low_priority) if low_priority else "_(none)_",

            '{next_step_1}': 'Run option [2] for detailed per-file review',
            '{next_step_2}': 'Or [3] for full report with all comments',
            '{next_step_3}': 'See references/checklist.md for the complete checklist'
        }
        
        output = self.template
        for placeholder, value in replacements.items():
            output = output.replace(placeholder, value)
        
        return output
    
    def fill_report_template(
        self,
        analysis: Dict,
        reviews: Dict,
        base: str,
        compare: str
    ) -> str:
        """Fills the full report template (assets/report.md)."""
        # This is more complex — simplified implementation
        # In practice, a structured reviews.json would be needed

        stats = analysis['stats']
        files = analysis['files']

        # Count issues by severity (from reviews.json)
        total_comments = sum(
            len(file_review.get('comments', []))
            for file_review in reviews.values()
        )
        
        replacements = {
            '{base_branch}': base,
            '{compare_branch}': compare,
            '{review_date}': datetime.now().strftime('%Y-%m-%d %H:%M'),
            '{files_reviewed}': str(len([f for f in files if f['path'].endswith('.py')])),
            '{total_comments}': str(total_comments),
            
            # These would need to be counted from reviews.json
            '{critical_count}': '0',
            '{high_count}': '0',
            '{medium_count}': '0',
            '{low_count}': '0',
            '{info_count}': '0',
            
            '{final_recommendation_emoji}': '✅',
            '{final_recommendation_text}': 'Aprovar',
            '{final_justification}': 'Review in progress — fill in after complete analysis',

            # Placeholder for detailed content
            '{detailed_reviews}': '_(Detailed reviews will be inserted here)_'
        }
        
        output = self.template
        for placeholder, value in replacements.items():
            output = output.replace(placeholder, value)
        
        return output
    
    def format(
        self,
        analysis_file: Optional[str] = None,
        reviews_file: Optional[str] = None,
        base: str = 'main',
        compare: str = 'HEAD'
    ) -> str:
        """Formats output based on the template."""

        # Load data
        analysis = None
        reviews = None

        if analysis_file:
            analysis = self.load_json(analysis_file)

        if reviews_file:
            reviews = self.load_json(reviews_file)

        # Determine which template to use based on name
        template_name = self.template_path.name
        
        if template_name == 'summary.md':
            if not analysis:
                raise ValueError("Analysis file required for summary template")
            return self.fill_summary_template(analysis, base, compare)
        
        elif template_name == 'report.md':
            if not analysis:
                raise ValueError("Analysis file required for report template")
            reviews = reviews or {}
            return self.fill_report_template(analysis, reviews, base, compare)
        
        elif template_name == 'comment.md':
            # Individual comment template — used directly during review
            return self.template

        else:
            # Generic template — return as-is
            return self.template


def main():
    parser = argparse.ArgumentParser(
        description='Format code review output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--template',
        required=True,
        help='Template file to use (from assets/)'
    )
    parser.add_argument(
        '--analysis',
        help='Analysis JSON file (from analyze_diff.py)'
    )
    parser.add_argument(
        '--reviews',
        help='Reviews JSON file (with comments)'
    )
    parser.add_argument(
        '--base',
        default='main',
        help='Base branch (default: main)'
    )
    parser.add_argument(
        '--compare',
        default='HEAD',
        help='Compare branch (default: HEAD)'
    )
    parser.add_argument(
        '--output',
        default='review-output.md',
        help='Output file (default: review-output.md)'
    )
    parser.add_argument(
        '--format',
        choices=['bitbucket', 'github', 'gitlab'],
        default='bitbucket',
        help='Output format (default: bitbucket)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create formatter
        formatter = OutputFormatter(args.template, args.format)

        # Generate output
        output = formatter.format(
            analysis_file=args.analysis,
            reviews_file=args.reviews,
            base=args.base,
            compare=args.compare
        )

        # Save
        with open(args.output, 'w') as f:
            f.write(output)
        
        print(f"✅ Review output saved to: {args.output}")
        print(f"📋 Template used: {args.template}")
        if args.analysis:
            print(f"📊 Analysis data: {args.analysis}")
        if args.reviews:
            print(f"💬 Reviews data: {args.reviews}")
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
