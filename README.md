# CCE Nodes Start/Stop Function

This serverless function is designed to start or stop Elastic Cloud Server (ECS) instances on Huawei Cloud. It's intended to be deployed on FunctionGraph.

## Features

- List ECS servers in a specified cluster
- Start ECS servers
- Stop ECS servers (with option for soft or hard stop)

## Prerequisites

- Huawei Cloud account
- Access Key (AK) and Secret Key (SK) with appropriate permissions
- Python 3.9 or later

## Dependencies

- `huaweicloudsdkcore`
- `huaweicloudsdkecs`

## Configuration

The function uses the following configuration parameters, which should be set as environment variables or function configurations in FunctionGraph:

- `projectId`: Your Huawei Cloud project ID
- `endpoint`: (Optional) The endpoint URL for the ECS service
- `region`: The region where your ECS instances are located
- `ak`: Access Key (can be overridden by FunctionGraph's built-in key)
- `sk`: Secret Key (can be overridden by FunctionGraph's built-in key)
- `type`: The stop type, either "SOFT" or "HARD" (default is "SOFT")
- `action`: The action to perform, either "start" or "stop"
- `clusterId`: (Optional) The ID of the CCE cluster to filter ECS instances

## Usage

The function can be triggered via FunctionGraph. The action (start or stop) and other parameters are determined by the function's configuration.

### Example Event

The function doesn't require any specific event structure. All necessary information is retrieved from the function's configuration.

```json
{}
```

## Function Behavior

1. The function first validates the configuration parameters.
2. It then establishes a connection to the ECS service using the provided credentials.
3. Depending on the specified action:
   - For "stop": It lists all servers in the specified cluster (or all if no cluster is specified) and then stops them.
   - For "start": It lists all servers in the specified cluster (or all if no cluster is specified) and then starts them.
4. The function returns a JSON object with the status of the operation, including any errors encountered.

## Return Value

The function returns a JSON object with the following structure:

```json
{
  "status": "success" or "error",
  "message": "Description of the result or error",
  "action": "start" or "stop",
  "data": {
    "server_list": [
      {"server_id": "id1", "server_name": "name1"},
      {"server_id": "id2", "server_name": "name2"},
      ...
    ]
  }
}
```

In case of an error, the `data` field may contain additional error information.

## Security Considerations

- Ensure that the AK/SK used have the minimum necessary permissions to perform the required actions on ECS instances.
- Be cautious when stopping instances, especially with the "HARD" stop type, as it may lead to data loss if instances are not properly shut down.

## Troubleshooting

- If you encounter authentication errors, verify that your AK/SK are correct and have the necessary permissions.
- For region-specific issues, ensure that the specified region matches the location of your ECS instances.
- Check the FunctionGraph logs for detailed error messages in case of failures.

## Contributing

Contributions to improve the function are welcome. Please submit a pull request or create an issue to discuss proposed changes.

## License

This function is licensed under the MIT License. See the LICENSE file for more information.

```txt
MIT License

Copyright (c) 2024 l2D

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
